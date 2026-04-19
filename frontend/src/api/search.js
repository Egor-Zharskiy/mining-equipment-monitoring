import { http } from './http'

export async function fetchGlobalSearch(params) {
  const response = await http.get('/search/', {
    params: {
      limit_per_section: 5,
      ...params,
    },
  })

  return response.data
}
