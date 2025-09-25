// API client for ETL operations - Fixed version
const API_BASE = `${import.meta.env.VITE_API_URL || 'http://localhost:8001'}/api/v1`

// ETL Job interface
export interface ETLJob {
  job_id: string
  filename: string
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled'
  progress: number
  created_at: string
  started_at?: string
  completed_at?: string
  error_message?: string
  total_records_processed: number
  successful_records: number
  failed_records: number
  validation_result?: {
    is_valid: boolean
    total_records: number
    issues: Array<{
      type: string
      message: string
      column?: string
      row_number?: number
    }>
  }
}

// Upload options interface
export interface UploadOptions {
  sheet_name?: string
  target_date?: string
  validate_only?: boolean
  overwrite_existing?: boolean
}

// Validation result interface
export interface ValidationResult {
  is_valid: boolean
  total_records: number
  issues: Array<{
    type: string
    message: string
    column?: string
    row_number?: number
  }>
}

// File upload and sheet analysis
export interface UploadedFile {
  file_id: string
  filename: string
  original_filename: string
  country: string
  file_size: number
  upload_date: string
  sheets: SheetInfo[]
  status: 'uploaded' | 'analyzing' | 'ready' | 'error'
}

export interface SheetInfo {
  sheet_name: string
  row_count: number
  column_count: number
  columns: string[]
  sample_data?: Record<string, unknown>[]
  validation_status: 'pending' | 'validated' | 'error'
  validation_result?: ValidationResult
  etl_status: 'not_loaded' | 'loading' | 'loaded' | 'failed'
  etl_job_id?: string
  loaded_at?: string
}

export interface FileAnalysisResult {
  file_id: string
  filename: string
  sheets: SheetInfo[]
  status: string
}

// ETL API class
export class ETLApi {
  private baseUrl: string

  constructor(baseUrl: string = API_BASE) {
    this.baseUrl = baseUrl
  }

  async uploadFile(file: File, options: UploadOptions = {}): Promise<ETLJob> {
    const formData = new FormData()
    formData.append('file', file)
    
    if (options.sheet_name) {
      formData.append('sheet_name', options.sheet_name)
    }
    if (options.target_date) {
      formData.append('target_date', options.target_date)
    }
    if (options.validate_only !== undefined) {
      formData.append('validate_only', options.validate_only.toString())
    }
    if (options.overwrite_existing !== undefined) {
      formData.append('overwrite_existing', options.overwrite_existing.toString())
    }

    const response = await fetch(`${this.baseUrl}/etl/upload`, {
      method: 'POST',
      body: formData,
    })

    if (!response.ok) {
      const error = await response.text()
      throw new Error(`Upload failed: ${error}`)
    }

    return response.json()
  }

  async uploadFileOnly(file: File, country: string): Promise<UploadedFile> {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('country', country)

    const response = await fetch(`${this.baseUrl}/etl/upload-file`, {
      method: 'POST',
      body: formData,
    })

    if (!response.ok) {
      const error = await response.text()
      throw new Error(`Upload failed: ${error}`)
    }

    return response.json()
  }

  async analyzeSheets(fileId: string): Promise<FileAnalysisResult> {
    const response = await fetch(`${this.baseUrl}/etl/files/${fileId}/analyze`)
    
    if (!response.ok) {
      const error = await response.text()
      throw new Error(`Analysis failed: ${error}`)
    }

    return response.json()
  }

  async validateSheets(fileId: string, sheetNames: string[]): Promise<Record<string, ValidationResult>> {
    
    const response = await fetch(`${this.baseUrl}/etl/files/${fileId}/validate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sheet_names: sheetNames }),
    })


    if (!response.ok) {
      const error = await response.text()
      throw new Error(`Validation failed: ${error}`)
    }

    return await response.json()
  }

  async confirmUpload(fileId: string, targetDate?: string): Promise<UploadedFile> {
    const response = await fetch(`${this.baseUrl}/etl/files/${fileId}/confirm`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ target_date: targetDate }),
    })

    if (!response.ok) {
      const error = await response.text()
      throw new Error(`Confirmation failed: ${error}`)
    }

    return response.json()
  }

  async processSheet(fileId: string, sheetName: string, targetDate: string): Promise<ETLJob> {
    const response = await fetch(`${this.baseUrl}/etl/files/${fileId}/sheets/${sheetName}/process`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ target_date: targetDate }),
    })

    if (!response.ok) {
      const error = await response.text()
      throw new Error(`Sheet processing failed: ${error}`)
    }

    return response.json()
  }

  async listFiles(): Promise<UploadedFile[]> {
    const response = await fetch(`${this.baseUrl}/etl/files`)
    
    if (!response.ok) {
      const error = await response.text()
      throw new Error(`Failed to list files: ${error}`)
    }

    return response.json()
  }

  async getFile(fileId: string): Promise<UploadedFile> {
    const response = await fetch(`${this.baseUrl}/etl/files/${fileId}`)
    
    if (!response.ok) {
      const error = await response.text()
      throw new Error(`Failed to get file: ${error}`)
    }

    return response.json()
  }

  async getJob(jobId: string): Promise<ETLJob> {
    const response = await fetch(`${this.baseUrl}/etl/jobs/${jobId}`)
    
    if (!response.ok) {
      const error = await response.text()
      throw new Error(`Failed to get job: ${error}`)
    }

    return response.json()
  }

  async listJobs(): Promise<ETLJob[]> {
    const response = await fetch(`${this.baseUrl}/etl/jobs`)
    
    if (!response.ok) {
      const error = await response.text()
      throw new Error(`Failed to list jobs: ${error}`)
    }

    return response.json()
  }

  // Legacy method for backward compatibility
  async validateFile(file: File, sheetName?: string): Promise<ValidationResult> {
    const formData = new FormData()
    formData.append('file', file)
    if (sheetName) {
      formData.append('sheet_name', sheetName)
    }

    const response = await fetch(`${this.baseUrl}/etl/validate`, {
      method: 'POST',
      body: formData,
    })

    if (!response.ok) {
      const error = await response.text()
      throw new Error(`Validation failed: ${error}`)
    }

    return response.json()
  }

  async cancelJob(jobId: string): Promise<void> {
    const response = await fetch(`${this.baseUrl}/etl/jobs/${jobId}/cancel`, {
      method: 'POST',
    })

    if (!response.ok) {
      const error = await response.text()
      throw new Error(`Failed to cancel job: ${error}`)
    }
  }

  async checkHealth(): Promise<{ status: string; service: string }> {
    const response = await fetch(`${this.baseUrl}/etl/health`)
    
    if (!response.ok) {
      throw new Error('ETL service is not available')
    }

    return response.json()
  }
}

// Export a singleton instance
export const etlApi = new ETLApi()