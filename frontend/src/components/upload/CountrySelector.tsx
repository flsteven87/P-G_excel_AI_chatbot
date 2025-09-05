// React import removed
import { Globe, MapPin } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Label } from '@/components/ui/label'

interface Country {
  code: string
  name: string
  flag: string
  description: string
}

const COUNTRIES: Country[] = [
  { 
    code: 'TW', 
    name: '台灣', 
    flag: '🇹🇼',
    description: '台灣地區庫存資料處理'
  },
  // 未來可擴展其他國家
  // { code: 'SG', name: '新加坡', flag: '🇸🇬', description: '新加坡地區庫存資料處理' },
]

interface CountrySelectorProps {
  selectedCountry: string
  onCountrySelect: (country: string) => void
}

export function CountrySelector({ selectedCountry, onCountrySelect }: CountrySelectorProps) {
  return (
    <div className="space-y-6">
      <div className="text-center space-y-2">
        <Globe className="h-12 w-12 mx-auto text-blue-600" />
        <h2 className="text-2xl font-bold">選擇資料來源國家</h2>
        <p className="text-muted-foreground">
          請選擇您要上傳的庫存資料所屬的國家或地區
        </p>
      </div>

      <div className="grid gap-4 max-w-md mx-auto">
        <Label className="text-base font-medium">可用國家/地區</Label>
        
        {COUNTRIES.map((country) => (
          <Card 
            key={country.code}
            className={`cursor-pointer transition-all hover:shadow-md ${
              selectedCountry === country.code 
                ? 'ring-2 ring-primary border-primary bg-primary/5' 
                : 'hover:border-primary/50'
            }`}
            onClick={() => onCountrySelect(country.code)}
          >
            <CardContent className="p-4">
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2">
                  <span className="text-2xl">{country.flag}</span>
                  <div>
                    <div className="font-medium">{country.name}</div>
                    <div className="text-sm text-muted-foreground">
                      {country.description}
                    </div>
                  </div>
                </div>
                
                {selectedCountry === country.code && (
                  <div className="ml-auto">
                    <div className="h-4 w-4 rounded-full bg-primary flex items-center justify-center">
                      <div className="h-2 w-2 rounded-full bg-white" />
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="text-center text-sm text-muted-foreground">
        <MapPin className="h-4 w-4 inline mr-1" />
        未來將支援更多國家和地區
      </div>
    </div>
  )
}