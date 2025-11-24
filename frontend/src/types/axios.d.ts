import 'axios'

declare module 'axios' {
  export interface AxiosRequestConfig<D = any> {
    skipAuthRefresh?: boolean
  }

  export interface InternalAxiosRequestConfig<D = any> {
    _retry?: boolean
  }
}
