import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined'
import { Alert } from '@mui/material'

export function DataFallbackNotice() {
  return (
    <Alert icon={<InfoOutlinedIcon fontSize="inherit" />} severity="info">
      Данные для этого экрана временно недоступны, поэтому показан резервный набор значений.
    </Alert>
  )
}
