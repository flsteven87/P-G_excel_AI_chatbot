import { useState, useCallback, useEffect, useRef } from 'react'
import { etlApi, UploadedFile, ETLJob } from '@/lib/api'

export interface FileManagerState {
  files: UploadedFile[]
  etlJobs: Record<string, ETLJob> // key: job_id
  isLoading: boolean
  error: string | null
}

export function useFileManager() {
  const [state, setState] = useState<FileManagerState>({
    files: [],
    etlJobs: {},
    isLoading: false,
    error: null,
  })

  const monitoringJobsRef = useRef<Set<string>>(new Set())

  const setError = useCallback((error: string | null) => {
    setState(prev => ({ ...prev, error, isLoading: false }))
  }, [])

  const clearError = useCallback(() => {
    setState(prev => ({ ...prev, error: null }))
  }, [])

  // Load all uploaded files
  const loadFiles = useCallback(async () => {
    try {
      setState(prev => ({ ...prev, isLoading: true, error: null }))
      
      const files = await etlApi.listFiles()
      
      setState(prev => ({ 
        ...prev, 
        files,
        isLoading: false,
      }))
    } catch (error) {
      setError(error instanceof Error ? error.message : '載入檔案列表失敗')
    }
  }, [setError])

  // Refresh specific file data
  const refreshFile = useCallback(async (fileId: string) => {
    try {
      const updatedFile = await etlApi.getFile(fileId)
      
      setState(prev => ({
        ...prev,
        files: prev.files.map(file => 
          file.file_id === fileId ? updatedFile : file
        ),
      }))
      
      return updatedFile
    } catch {
      // Error handled by parent component
    }
  }, [])

  // Process a specific sheet
  const processSheet = useCallback(async (fileId: string, sheetName: string, targetDate: string) => {
    try {
      // Check if sheet is already loaded
      const file = state.files.find(f => f.file_id === fileId)
      const sheet = file?.sheets.find(s => s.sheet_name === sheetName)
      
      if (sheet?.etl_status === 'loaded') {
        setError(`Sheet "${sheetName}" 已經載入過了`)
        return null
      }

      // 立即更新 UI 狀態為載入中
      setState(prev => ({
        ...prev,
        files: prev.files.map(file => {
          if (file.file_id === fileId) {
            return {
              ...file,
              sheets: file.sheets.map(s => {
                if (s.sheet_name === sheetName) {
                  return {
                    ...s,
                    etl_status: 'loading' as const,
                  }
                }
                return s
              })
            }
          }
          return file
        }),
      }))

      const etlJob = await etlApi.processSheet(fileId, sheetName, targetDate)
      
      setState(prev => ({
        ...prev,
        etlJobs: { ...prev.etlJobs, [etlJob.job_id]: etlJob },
        files: prev.files.map(file => {
          if (file.file_id === fileId) {
            return {
              ...file,
              sheets: file.sheets.map(s => {
                if (s.sheet_name === sheetName) {
                  return {
                    ...s,
                    etl_status: 'loading' as const,
                    etl_job_id: etlJob.job_id,
                  }
                }
                return s
              })
            }
          }
          return file
        }),
      }))

      // Start monitoring the job
      startJobMonitoring(etlJob.job_id, fileId, sheetName)
      
      return etlJob
    } catch (error) {
      
      // 恢復 UI 狀態
      setState(prev => ({
        ...prev,
        files: prev.files.map(file => {
          if (file.file_id === fileId) {
            return {
              ...file,
              sheets: file.sheets.map(s => {
                if (s.sheet_name === sheetName) {
                  return {
                    ...s,
                    etl_status: 'failed' as const,
                  }
                }
                return s
              })
            }
          }
          return file
        }),
      }))
      
      setError(error instanceof Error ? error.message : '處理失敗')
      return null
    }
  }, [state.files, setError])

  // Monitor ETL job progress
  const startJobMonitoring = useCallback((jobId: string, fileId: string, sheetName: string) => {
    if (monitoringJobsRef.current.has(jobId)) {
      return // Already monitoring
    }

    monitoringJobsRef.current.add(jobId)

    const pollJob = async () => {
      try {
        const updatedJob = await etlApi.getJob(jobId)
        
        setState(prev => ({
          ...prev,
          etlJobs: { ...prev.etlJobs, [jobId]: updatedJob },
          files: prev.files.map(file => {
            if (file.file_id === fileId) {
              return {
                ...file,
                sheets: file.sheets.map(sheet => {
                  if (sheet.sheet_name === sheetName) {
                    let newEtlStatus = sheet.etl_status
                    
                    // 映射後端狀態到前端狀態
                    switch (updatedJob.status) {
                      case 'completed':
                        newEtlStatus = 'loaded'
                        break
                      case 'failed':
                      case 'cancelled':
                        newEtlStatus = 'failed'
                        break
                      case 'processing':
                        newEtlStatus = 'loading'
                        break
                      case 'pending':
                        newEtlStatus = 'loading' // 顯示為載入中
                        break
                      default:
                        newEtlStatus = sheet.etl_status // 保持原狀態
                    }
                    
                    return {
                      ...sheet,
                      etl_status: newEtlStatus,
                      loaded_at: updatedJob.completed_at,
                    }
                  }
                  return sheet
                })
              }
            }
            return file
          }),
        }))

        // Continue polling if job is still running
        const activeStatuses = ['pending', 'processing', 'validating', 'loading']
        if (activeStatuses.includes(updatedJob.status)) {
          setTimeout(pollJob, 2000) // Poll every 2 seconds for faster updates
        } else {
          monitoringJobsRef.current.delete(jobId)
        }
      } catch (error) {
        monitoringJobsRef.current.delete(jobId)
      }
    }

    // Start polling after 1 second
    setTimeout(pollJob, 1000)
  }, [])

  // Cancel ETL job
  const cancelJob = useCallback(async (jobId: string) => {
    try {
      await etlApi.cancelJob(jobId)
      
      setState(prev => ({
        ...prev,
        etlJobs: {
          ...prev.etlJobs,
          [jobId]: { ...prev.etlJobs[jobId], status: 'cancelled' }
        },
      }))
    } catch (error) {
      setError(error instanceof Error ? error.message : '取消失敗')
    }
  }, [setError])

  // Add file to list (called after wizard completion)
  const addFile = useCallback((file: UploadedFile) => {
    setState(prev => ({
      ...prev,
      files: [file, ...prev.files],
    }))
  }, [])

  // Get sheet ETL status
  const getSheetEtlStatus = useCallback((fileId: string, sheetName: string) => {
    const file = state.files.find(f => f.file_id === fileId)
    const sheet = file?.sheets.find(s => s.sheet_name === sheetName)
    return sheet?.etl_status || 'not_loaded'
  }, [state.files])

  // Get ETL job for sheet
  const getSheetETLJob = useCallback((fileId: string, sheetName: string): ETLJob | null => {
    const file = state.files.find(f => f.file_id === fileId)
    const sheet = file?.sheets.find(s => s.sheet_name === sheetName)
    const jobId = sheet?.etl_job_id
    return jobId ? (state.etlJobs[jobId] || null) : null
  }, [state.files, state.etlJobs])

  // Check if sheet can be processed (not already loaded)
  const canProcessSheet = useCallback((fileId: string, sheetName: string): boolean => {
    const status = getSheetEtlStatus(fileId, sheetName)
    return status === 'not_loaded' || status === 'failed'
  }, [getSheetEtlStatus])

  // Auto-load files on mount
  useEffect(() => {
    loadFiles()
  }, [loadFiles])

  return {
    state,
    loadFiles,
    refreshFile,
    processSheet,
    cancelJob,
    addFile,
    getSheetEtlStatus,
    getSheetETLJob,
    canProcessSheet,
    setError,
    clearError,
  }
}