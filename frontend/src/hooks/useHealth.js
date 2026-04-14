import { useState, useEffect, useCallback } from 'react'
import { getHealth } from '../api'

export function useHealth() {
  const [health, setHealth] = useState({ status: 'unknown', indexed_docs: 0 })

  const refresh = useCallback(async () => {
    try {
      const data = await getHealth()
      setHealth(data)
    } catch {
      setHealth({ status: 'error', indexed_docs: 0 })
    }
  }, [])

  useEffect(() => {
    refresh()
    const id = setInterval(refresh, 8000)
    return () => clearInterval(id)
  }, [refresh])

  return { health, refresh }
}
