import { ArrowLeft, ArrowRight, X, CheckCircle } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Stepper } from '@/components/ui/stepper'
import { CountrySelector } from './CountrySelector'
import { FileUploader } from './FileUploader'
import { SheetSelector } from './SheetSelector'
import { ConfirmationStep } from './ConfirmationStep'
import { useUploadWizard } from '@/hooks/useUploadWizard'

interface UploadWizardProps {
  isOpen: boolean
  onClose: () => void
  onComplete: (uploadedFile: unknown) => void
}

export function UploadWizard({ isOpen, onClose, onComplete }: UploadWizardProps) {
  const {
    state,
    steps,
    nextStep,
    prevStep,
    selectCountry,
    selectFile,
    analyzeSheets,
    toggleSheet,
    validateSelectedSheets,
    confirmUpload,
    clearError,
    getCurrentStepData,
  } = useUploadWizard()

  const stepData = getCurrentStepData()
  const { step, canGoNext, canGoPrev, isLastStep } = stepData

  if (!isOpen) return null

  const handleNext = async () => {
    let success = true

    // Execute step-specific actions
    switch (state.currentStep) {
      case 0: // Country selection - no action needed, just move to next step
        success = true
        break
      case 1: // File selection - no action needed, just move to next step
        success = true
        break
      case 2: // Upload and analyze - this now happens automatically, so just wait or skip
        // Step 2 的上傳和分析由 useEffect 自動處理，這裡不需要做任何事
        success = !!state.uploadedFile && state.uploadedFile.sheets.length > 0
        break
      case 3: // Select sheets - no action needed, just move to next step
        success = true
        break
      case 4: // Validate and confirm upload - final step
        success = await validateSelectedSheets()
        if (success) {
          success = await confirmUpload()
          if (success && state.uploadedFile) {
            // 成功回饋
            setTimeout(() => {
              onComplete(state.uploadedFile)
              handleClose()
            }, 800) // 短暫延遲讓用戶看到成功狀態
            return // 直接返回，不需要調用 nextStep()
          }
        }
        break
    }

    if (success && state.currentStep < steps.length - 1) {
      nextStep()
    }
  }

  const handleClose = () => {
    onClose()
  }

  const renderStepContent = () => {
    switch (state.currentStep) {
      case 0:
        return (
          <CountrySelector
            selectedCountry={state.selectedCountry}
            onCountrySelect={selectCountry}
          />
        )
      
      case 1:
        return (
          <FileUploader
            selectedFile={state.selectedFile}
            onFileSelect={selectFile}
            selectedCountry={state.selectedCountry}
          />
        )
        
      case 2:
        return (
          <div className="space-y-6">
            <div className="text-center space-y-2">
              <div className="h-12 w-12 mx-auto rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center">
                <div className="h-6 w-6 animate-spin rounded-full border-2 border-current border-t-transparent" />
              </div>
              <h2 className="text-2xl font-bold">上傳並分析中...</h2>
              <p className="text-muted-foreground">
                正在上傳檔案並分析工作表，請稍候...
              </p>
            </div>
            
            {state.uploadedFile && state.uploadedFile.sheets.length > 0 && (
              <div className="text-center space-y-2">
                <div className="text-green-600 font-medium">✅ 分析完成！</div>
                <p className="text-sm text-muted-foreground">
                  發現 {state.uploadedFile.sheets.length} 個工作表，正在跳轉到工作表選擇...
                </p>
              </div>
            )}
          </div>
        )
        
      case 3:
        return (
          <SheetSelector
            sheets={state.uploadedFile?.sheets || []}
            selectedSheets={state.selectedSheets}
            onToggleSheet={toggleSheet}
            onAnalyzeSheets={analyzeSheets}
            isAnalyzing={state.isLoading}
          />
        )
        
      case 4:
        return (
          <ConfirmationStep
            filename={state.uploadedFile?.original_filename || ''}
            selectedCountry={state.selectedCountry}
            selectedSheets={state.selectedSheets}
            validationResults={state.validationResults}
            targetDate={state.targetDate}
            onTargetDateChange={() => {
              // Update target date in state
            }}
          />
        )
        
      default:
        return <div>未知步驟</div>
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-background rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <Card className="border-0 shadow-none">
          <CardHeader className="text-center border-b">
            <CardTitle className="text-2xl">Excel ETL 上傳嚮導</CardTitle>
            <div className="mt-6">
              <Stepper
                steps={steps}
                currentStep={state.currentStep}
                completedSteps={state.completedSteps}
              />
            </div>
          </CardHeader>

          <CardContent className="p-8">
            {/* Error Display */}
            {state.error && (
              <Alert variant="destructive" className="mb-6">
                <AlertTitle>錯誤</AlertTitle>
                <AlertDescription className="flex items-center justify-between">
                  {state.error}
                  <Button variant="ghost" size="sm" onClick={clearError}>
                    <X className="h-4 w-4" />
                  </Button>
                </AlertDescription>
              </Alert>
            )}

            {/* Step Content */}
            <div className="min-h-96">
              {renderStepContent()}
            </div>
          </CardContent>

          {/* Navigation Footer */}
          <div className="border-t p-6">
            <div className="flex items-center justify-between">
              <div className="flex space-x-2">
                <Button variant="ghost" onClick={handleClose}>
                  取消
                </Button>
              </div>

              <div className="flex space-x-2">
                {canGoPrev && (
                  <Button variant="outline" onClick={prevStep} disabled={state.isLoading}>
                    <ArrowLeft className="h-4 w-4 mr-2" />
                    上一步
                  </Button>
                )}
                
                <Button
                  onClick={canGoNext ? handleNext : undefined}
                  disabled={!canGoNext || state.isLoading}
                >
                  {state.isLoading ? (
                    <div className="h-4 w-4 mr-2 animate-spin rounded-full border-2 border-current border-t-transparent" />
                  ) : isLastStep ? (
                    <CheckCircle className="h-4 w-4 mr-2" />
                  ) : (
                    <ArrowRight className="h-4 w-4 mr-2" />
                  )}
                  
                  {state.isLoading ? '處理中...' : (
                    isLastStep ? '完成上傳' : '下一步'
                  )}
                </Button>
              </div>
            </div>

            {/* Step Info */}
            <div className="text-center mt-4 text-sm text-muted-foreground">
              步驟 {state.currentStep + 1} / {steps.length}: {step.description}
            </div>
          </div>
        </Card>
      </div>
    </div>
  )
}