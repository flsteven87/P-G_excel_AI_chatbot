import * as React from "react"
import { ChevronDown, Check } from "lucide-react"
import { cn } from "@/lib/utils"

export interface SelectProps {
  value?: string
  onValueChange?: (value: string) => void
  placeholder?: string
  children: React.ReactNode
  disabled?: boolean
}

export interface SelectItemProps {
  value: string
  children: React.ReactNode
  disabled?: boolean
}

const Select = React.forwardRef<HTMLDivElement, SelectProps>(
  ({ value, onValueChange, placeholder, children, disabled, ...props }, ref) => {
    const [open, setOpen] = React.useState(false)
    const [selectedValue, setSelectedValue] = React.useState(value)

    // handleSelect removed as it was not being used in current implementation

    React.useEffect(() => {
      setSelectedValue(value)
    }, [value])

    return (
      <div className="relative" ref={ref} {...props}>
        <button
          type="button"
          className={cn(
            "flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50",
            disabled && "opacity-50 cursor-not-allowed"
          )}
          onClick={() => !disabled && setOpen(!open)}
          disabled={disabled}
        >
          <span>{selectedValue || placeholder}</span>
          <ChevronDown className="h-4 w-4 opacity-50" />
        </button>
        {open && (
          <div className="absolute top-full z-50 w-full mt-1 bg-popover text-popover-foreground rounded-md border shadow-md">
            {React.Children.map(children, (child) => {
              if (React.isValidElement(child)) {
                return child
              }
              return child
            })}
          </div>
        )}
      </div>
    )
  }
)
Select.displayName = "Select"

const SelectItem = React.forwardRef<HTMLDivElement, SelectItemProps & { onSelect?: (value: string) => void, selected?: boolean }>(
  ({ value, children, disabled, onSelect, selected, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          "relative flex w-full cursor-default select-none items-center rounded-sm py-1.5 px-2 text-sm outline-none hover:bg-accent hover:text-accent-foreground focus:bg-accent focus:text-accent-foreground data-[disabled]:pointer-events-none data-[disabled]:opacity-50",
          disabled && "pointer-events-none opacity-50"
        )}
        onClick={() => !disabled && onSelect?.(value)}
        {...props}
      >
        {selected && <Check className="h-4 w-4 mr-2" />}
        <span className={cn(selected ? "ml-0" : "ml-6")}>{children}</span>
      </div>
    )
  }
)
SelectItem.displayName = "SelectItem"

const SelectContent = ({ children }: { children: React.ReactNode }) => {
  return <>{children}</>
}
SelectContent.displayName = "SelectContent"

const SelectValue = ({ placeholder }: { placeholder?: string }) => {
  return <span>{placeholder}</span>
}
SelectValue.displayName = "SelectValue"

export { Select, SelectItem, SelectContent, SelectValue }