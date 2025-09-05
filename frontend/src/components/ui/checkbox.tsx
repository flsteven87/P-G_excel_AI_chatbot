import * as React from "react"
import { Check } from "lucide-react"
import { cn } from "@/lib/utils"

export interface CheckboxProps
  extends React.InputHTMLAttributes<HTMLInputElement> {}

const Checkbox = React.forwardRef<HTMLInputElement, CheckboxProps>(
  ({ className, ...props }, ref) => (
    <label className="relative inline-flex items-center cursor-pointer">
      <input
        type="checkbox"
        className="sr-only"
        ref={ref}
        {...props}
      />
      <div
        className={cn(
          "peer relative h-4 w-4 shrink-0 rounded-sm border border-primary ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 data-[state=checked]:bg-primary data-[state=checked]:text-primary-foreground",
          className
        )}
      >
        <Check 
          className={cn(
            "h-4 w-4 absolute inset-0 opacity-0 peer-checked:opacity-100 transition-opacity text-primary-foreground"
          )}
        />
      </div>
    </label>
  )
)
Checkbox.displayName = "Checkbox"

export { Checkbox }