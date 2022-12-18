import type { AxiosInstance } from 'axios'
import axios from 'axios'

const axiosConfig = {
  baseURL: process.env.VUE_APP_PUBLICPATH,
  timeout: 300000
}

const apiClient: AxiosInstance = axios.create(axiosConfig)

export default apiClient
