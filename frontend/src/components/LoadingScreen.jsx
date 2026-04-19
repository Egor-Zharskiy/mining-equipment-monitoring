import { Box, CircularProgress, Typography } from '@mui/material'

export function LoadingScreen({ label = 'Загрузка рабочего пространства' }) {
  return (
    <Box
      sx={{
        alignItems: 'center',
        display: 'flex',
        flexDirection: 'column',
        gap: 2,
        justifyContent: 'center',
        minHeight: '100vh',
      }}
    >
      <CircularProgress color="primary" size={40} />
      <Typography color="text.secondary">{label}</Typography>
    </Box>
  )
}
