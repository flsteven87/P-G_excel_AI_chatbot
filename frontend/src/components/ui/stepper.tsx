// React import removed
import { Check } from 'lucide-react'
import { cn } from '@/lib/utils'

interface Step {
  id: string
  title: string
  description?: string
}

interface StepperProps {
  steps: Step[]
  currentStep: number
  completedSteps: number[]
  className?: string
}

export function Stepper({ steps, currentStep, completedSteps, className }: StepperProps) {
  return (
    <div className={cn("w-full", className)}>
      <nav aria-label="Progress">
        <ol className="flex items-center justify-center space-x-4 md:space-x-8">
          {steps.map((step, index) => {
            const isCompleted = completedSteps.includes(index)
            const isCurrent = index === currentStep
            const isUpcoming = index > currentStep

            return (
              <li key={step.id} className="flex items-center">
                <div className="flex flex-col items-center">
                  {/* Step Circle */}
                  <div
                    className={cn(
                      "flex h-10 w-10 items-center justify-center rounded-full border-2 text-sm font-semibold",
                      {
                        "border-primary bg-primary text-primary-foreground": isCompleted,
                        "border-primary bg-background text-primary": isCurrent,
                        "border-muted bg-muted text-muted-foreground": isUpcoming,
                      }
                    )}
                  >
                    {isCompleted ? (
                      <Check className="h-6 w-6" />
                    ) : (
                      <span>{index + 1}</span>
                    )}
                  </div>

                  {/* Step Content */}
                  <div className="mt-2 text-center">
                    <div
                      className={cn(
                        "text-sm font-medium",
                        {
                          "text-foreground": isCompleted || isCurrent,
                          "text-muted-foreground": isUpcoming,
                        }
                      )}
                    >
                      {step.title}
                    </div>
                    {step.description && (
                      <div className="text-xs text-muted-foreground mt-1 max-w-20">
                        {step.description}
                      </div>
                    )}
                  </div>
                </div>

                {/* Connector Line */}
                {index < steps.length - 1 && (
                  <div
                    className={cn(
                      "ml-4 h-px w-12 md:w-20",
                      {
                        "bg-primary": isCompleted,
                        "bg-muted": !isCompleted,
                      }
                    )}
                  />
                )}
              </li>
            )
          })}
        </ol>
      </nav>
    </div>
  )
}