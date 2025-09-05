import { useState, useCallback, useEffect } from 'react'
import { etlApi, UploadedFile, ValidationResult } from '@/lib/api'

export interface WizardStep {
  id: string
  title: string
  description: string
}

export interface WizardState {
  currentStep: number
  completedSteps: number[]
  selectedCountry: string
  selectedFile: File | null
  uploadedFile: UploadedFile | null
  selectedSheets: string[]
  validationResults: Record<string, ValidationResult>
  targetDate: string
  isLoading: boolean
  error: string | null
}

export const WIZARD_STEPS: WizardStep[] = [
  { id: 'country', title: '選擇國家', description: '選擇資料來源國家' },
  { id: 'file', title: '選擇檔案', description: '選擇要上傳的 Excel 檔案' },
  { id: 'upload', title: '上傳分析', description: '上傳檔案並分析工作表' },
  { id: 'sheets', title: '選擇工作表', description: '選擇要處理的工作表' },
  { id: 'confirm', title: '驗證完成', description: '驗證資料並完成上傳' },
]

export function useUploadWizard() {
  const [state, setState] = useState<WizardState>({
    currentStep: 0,
    completedSteps: [],
    selectedCountry: 'TW',
    selectedFile: null,
    uploadedFile: null,
    selectedSheets: [],
    validationResults: {},
    targetDate: new Date().toISOString().split('T')[0],
    isLoading: false,
    error: null,
  })

  const setError = useCallback((error: string | null) => {
    setState(prev => ({ ...prev, error, isLoading: false }))
  }, [])

  const clearError = useCallback(() => {
    setState(prev => ({ ...prev, error: null }))
  }, [])

  const nextStep = useCallback(() => {
    setState(prev => {
      const newCurrentStep = Math.min(prev.currentStep + 1, WIZARD_STEPS.length - 1)
      const newCompletedSteps = [...new Set([...prev.completedSteps, prev.currentStep])]
      
      return {
        ...prev,
        currentStep: newCurrentStep,
        completedSteps: newCompletedSteps,
        error: null,
      }
    })
  }, [])

  const prevStep = useCallback(() => {
    setState(prev => ({
      ...prev,
      currentStep: Math.max(prev.currentStep - 1, 0),
      error: null,
    }))
  }, [])

  const goToStep = useCallback((stepIndex: number) => {
    if (stepIndex >= 0 && stepIndex < WIZARD_STEPS.length) {
      setState(prev => ({
        ...prev,
        currentStep: stepIndex,
        error: null,
      }))
    }
  }, [])

  // Step 1: Select Country
  const selectCountry = useCallback((country: string) => {
    setState(prev => ({ ...prev, selectedCountry: country }))
  }, [])

  // Step 2: Upload File
  const selectFile = useCallback((file: File | null) => {
    setState(prev => ({ 
      ...prev, 
      selectedFile: file,
      uploadedFile: null,
      selectedSheets: [],
      validationResults: {},
    }))
  }, [])

  const uploadFile = useCallback(async () => {
    if (!state.selectedFile || !state.selectedCountry) {
      setError('請選擇檔案和國家')
      return false
    }

    try {
      setState(prev => ({ ...prev, isLoading: true, error: null }))
      
      
      const uploadedFile = await etlApi.uploadFileOnly(state.selectedFile, state.selectedCountry)
      
      
      // 驗證響應數據
      if (!uploadedFile || !uploadedFile.file_id) {
        setError('檔案上傳失敗: 服務器響應無效')
        return false
      }
      
      setState(prev => ({ 
        ...prev, 
        uploadedFile,
        isLoading: false,
      }))
      
      return true
    } catch (error) {
      let errorMessage = '未知錯誤'
      if (error instanceof Error) {
        errorMessage = error.message
        // 提取更詳細的錯誤信息
        if (error.message.includes('Upload failed:')) {
          errorMessage = error.message.replace('Upload failed: ', '')
        }
      }
      setError(`檔案上傳失敗: ${errorMessage}`)
      return false
    }
  }, [state.selectedFile, state.selectedCountry, setError])

  // Step 3: Analyze Sheets (after upload)
  const analyzeSheets = useCallback(async () => {
    // 在新流程中，這個函數被呼叫時 uploadedFile 應該已經存在（由 uploadFile 建立）
    
    if (!state.uploadedFile) {
      setError('檔案上傳失敗，無法分析工作表。請重新嘗試上傳。')
      return false
    }

    if (!state.uploadedFile.file_id) {
      setError('檔案 ID 無效，無法分析工作表')
      return false
    }

    try {
      setState(prev => ({ ...prev, isLoading: true, error: null }))
      
      const analysis = await etlApi.analyzeSheets(state.uploadedFile.file_id)
      
      if (!analysis || !Array.isArray(analysis.sheets)) {
        setError('工作表分析失敗: 服務器響應無效')
        return false
      }
      
      setState(prev => ({ 
        ...prev, 
        uploadedFile: {
          ...prev.uploadedFile!,
          sheets: analysis.sheets
        },
        isLoading: false,
      }))
      
      return true
    } catch (error) {
      let errorMessage = 'Sheet 分析失敗'
      if (error instanceof Error) {
        errorMessage = error.message
        if (error.message.includes('Analysis failed:')) {
          errorMessage = error.message.replace('Analysis failed: ', '')
        }
      }
      setError(`工作表分析失敗: ${errorMessage}`)
      return false
    }
  }, [state.uploadedFile, setError])

  const toggleSheet = useCallback((sheetName: string) => {
    setState(prev => {
      const isSelected = prev.selectedSheets.includes(sheetName)
      const newSelectedSheets = isSelected
        ? prev.selectedSheets.filter(name => name !== sheetName)
        : [...prev.selectedSheets, sheetName]
      
      return { ...prev, selectedSheets: newSelectedSheets }
    })
  }, [])

  // Step 4: Validate Selected Sheets
  const validateSelectedSheets = useCallback(async () => {
    if (!state.uploadedFile || state.selectedSheets.length === 0) {
      setError('請選擇要驗證的 Sheets')
      return false
    }

    try {
      setState(prev => ({ ...prev, isLoading: true, error: null }))
      
      const validationResults = await etlApi.validateSheets(
        state.uploadedFile.file_id, 
        state.selectedSheets
      )
      
      setState(prev => ({ 
        ...prev, 
        validationResults,
        isLoading: false,
      }))
      
      return true
    } catch (error) {
      setError(error instanceof Error ? error.message : '驗證失敗')
      return false
    }
  }, [state.uploadedFile, state.selectedSheets, setError])

  // Step 5: Confirm Upload
  const confirmUpload = useCallback(async () => {
    if (!state.uploadedFile) {
      setError('沒有要確認的檔案')
      return false
    }

    try {
      setState(prev => ({ ...prev, isLoading: true, error: null }))
      
      const confirmedFile = await etlApi.confirmUpload(state.uploadedFile.file_id, state.targetDate)
      
      setState(prev => ({ 
        ...prev, 
        uploadedFile: confirmedFile,
        isLoading: false,
      }))
      
      return true
    } catch (error) {
      setError(error instanceof Error ? error.message : '確認上傳失敗')
      return false
    }
  }, [state.uploadedFile, setError])

  // 當進入 Step 2 時自動執行上傳和分析
  const autoUploadAndAnalyze = useCallback(async () => {
    if (state.currentStep === 2 && !state.isLoading && !state.uploadedFile && state.selectedFile && state.selectedCountry) {
      
      try {
        setState(prev => ({ ...prev, isLoading: true, error: null }))
        
        // 1. 先上傳檔案
        const uploadedFile = await etlApi.uploadFileOnly(state.selectedFile, state.selectedCountry)
        
        
        // 2. 分析工作表
        const analysis = await etlApi.analyzeSheets(uploadedFile.file_id)
        
        
        // 3. 更新狀態
        setState(prev => ({ 
          ...prev, 
          uploadedFile: {
            ...uploadedFile,
            sheets: analysis.sheets
          },
          isLoading: false,
        }))
        
        // 4. 短暫延遲後自動跳轉
        setTimeout(() => {
          nextStep()
        }, 1000)
        
      } catch (error) {
        setError(`檔案處理失敗: ${error instanceof Error ? error.message : '未知錯誤'}`)
      }
    }
  }, [state.currentStep, state.isLoading, state.uploadedFile, state.selectedFile, state.selectedCountry, nextStep, setError])

  // 監聽步驟變化，當進入 Step 2 時自動執行上傳和分析
  useEffect(() => {
    autoUploadAndAnalyze()
  }, [autoUploadAndAnalyze])


  const canGoNext = useCallback(() => {
    switch (state.currentStep) {
      case 0: // Country selection
        return !!state.selectedCountry
      case 1: // File selection  
        return !!state.selectedFile
      case 2: // Upload and analyze - Step 2 現在是自動處理，不需要手動點擊
        return false // Step 2 會自動跳轉，禁用手動下一步
      case 3: // Sheet selection
        return state.selectedSheets.length > 0
      case 4: // Validation and confirmation - final step
        return true
      default:
        return false
    }
  }, [state])

  const getCurrentStepData = useCallback(() => {
    return {
      step: WIZARD_STEPS[state.currentStep],
      canGoNext: canGoNext(),
      canGoPrev: state.currentStep > 0,
      isLastStep: state.currentStep === WIZARD_STEPS.length - 1,
    }
  }, [state.currentStep, canGoNext])

  return {
    state,
    steps: WIZARD_STEPS,
    nextStep,
    prevStep,
    goToStep,
    selectCountry,
    selectFile,
    uploadFile,
    analyzeSheets,
    toggleSheet,
    validateSelectedSheets,
    confirmUpload,
    setError,
    clearError,
    getCurrentStepData,
  }
}