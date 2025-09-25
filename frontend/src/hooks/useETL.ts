import { useState, useCallback, useRef, useEffect } from 'react'
import { etlApi, ETLJob, UploadOptions } from '@/lib/api'

export interface ETLState {
  jobs: ETLJob[]
  isUploading: boolean
  isValidating: boolean
  isLoading: boolean
  error: string | null
}

export function useETL() {
  const [state, setState] = useState<ETLState>({
    jobs: [],
    isUploading: false,
    isValidating: false,
    isLoading: false,
    error: null,
  })

  const monitoringJobsRef = useRef<Set<string>>(new Set())

  // Load existing jobs
  const loadJobs = useCallback(async () => {
    try {
      setState(prev => ({ ...prev, isLoading: true, error: null }))
      const jobs = await etlApi.listJobs()
      setState(prev => ({ ...prev, jobs, isLoading: false }))
    } catch (error) {
      setState(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : 'Failed to load jobs',
        isLoading: false,
      }))
    }
  }, [])

  // Upload file
  const uploadFile = useCallback(async (file: File, options: UploadOptions = {}) => {
    try {
      setState(prev => ({ ...prev, isUploading: true, error: null }))
      
      const job = await etlApi.uploadFile(file, options)
      
      setState(prev => ({
        ...prev,
        jobs: [job, ...prev.jobs],
        isUploading: false,
      }))

      // Start monitoring the job
      startJobMonitoring(job.job_id)

      return job
    } catch (error) {
      setState(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : 'Upload failed',
        isUploading: false,
      }))
      throw error
    }
  }, [])

  // Validate file only
  const validateFile = useCallback(async (file: File, sheetName?: string) => {
    try {
      setState(prev => ({ ...prev, isValidating: true, error: null }))
      
      const result = await etlApi.validateFile(file, sheetName)
      
      setState(prev => ({ ...prev, isValidating: false }))
      
      return result
    } catch (error) {
      setState(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : 'Validation failed',
        isValidating: false,
      }))
      throw error
    }
  }, [])

  // Monitor job progress
  const startJobMonitoring = useCallback((jobId: string) => {
    if (monitoringJobsRef.current.has(jobId)) {
      return // Already monitoring
    }

    monitoringJobsRef.current.add(jobId)

    const pollJob = async () => {
      try {
        const updatedJob = await etlApi.getJob(jobId)
        
        setState(prev => ({
          ...prev,
          jobs: prev.jobs.map(job => 
            job.job_id === jobId ? updatedJob : job
          ),
        }))

        // Continue polling if job is still running
        if (updatedJob.status === 'pending' || updatedJob.status === 'processing') {
          setTimeout(pollJob, 2000) // Poll every 2 seconds
        } else {
          monitoringJobsRef.current.delete(jobId)
        }
      } catch {
        monitoringJobsRef.current.delete(jobId)
      }
    }

    // Start polling
    setTimeout(pollJob, 1000)
  }, [])

  // Cancel job
  const cancelJob = useCallback(async (jobId: string) => {
    try {
      await etlApi.cancelJob(jobId)
      
      // Update job status locally
      setState(prev => ({
        ...prev,
        jobs: prev.jobs.map(job =>
          job.job_id === jobId
            ? { ...job, status: 'cancelled' as const }
            : job
        ),
      }))
    } catch (error) {
      setState(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : 'Failed to cancel job',
      }))
    }
  }, [])

  // Refresh job status
  const refreshJob = useCallback(async (jobId: string) => {
    try {
      const updatedJob = await etlApi.getJob(jobId)
      
      setState(prev => ({
        ...prev,
        jobs: prev.jobs.map(job => 
          job.job_id === jobId ? updatedJob : job
        ),
      }))
      
      return updatedJob
    } catch {
      // Error handled by parent component
    }
  }, [])

  // Clear error
  const clearError = useCallback(() => {
    setState(prev => ({ ...prev, error: null }))
  }, [])

  // Check if file already exists (prevent duplicates)
  const hasFileBeenUploaded = useCallback((filename: string) => {
    return state.jobs.some(job => 
      job.filename === filename && 
      (job.status === 'completed' || job.status === 'processing' || job.status === 'pending')
    )
  }, [state.jobs])

  // Auto-load jobs on mount
  useEffect(() => {
    loadJobs()
  }, [loadJobs])

  return {
    ...state,
    loadJobs,
    uploadFile,
    validateFile,
    cancelJob,
    refreshJob,
    clearError,
    hasFileBeenUploaded,
  }
}