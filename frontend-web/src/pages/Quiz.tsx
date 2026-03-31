import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'

export default function Quiz() {
  const navigate = useNavigate()
  useEffect(() => { navigate('/dashboard', { replace: true }) }, [])
  return null
}
