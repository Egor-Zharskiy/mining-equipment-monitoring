import TrendingUpRoundedIcon from '@mui/icons-material/TrendingUpRounded'
import { useTheme } from '@mui/material/styles'
import { alpha } from '@mui/material/styles'
import { Box, Paper, Stack, Typography } from '@mui/material'

export function StatCard({ label, value, hint, accent = 'primary.main' }) {
  const theme = useTheme()
  const [paletteKey, shadeKey] = String(accent).split('.')
  const resolvedAccent = theme.palette[paletteKey]?.[shadeKey] ?? accent

  return (
    <Paper
      sx={{
        border: '1px solid',
        borderColor: 'divider',
        p: 2.5,
        position: 'relative',
        overflow: 'hidden',
      }}
    >
        <Box
          sx={{
            position: 'absolute',
            inset: 'auto -40px -50px auto',
            width: 120,
            height: 120,
            borderRadius: '50%',
            background: `radial-gradient(circle, ${alpha(resolvedAccent, 0.22)} 0%, transparent 72%)`,
          }}
        />
      <Stack direction="row" spacing={2} sx={{ alignItems: 'flex-start', justifyContent: 'space-between' }}>
        <Box>
          <Typography color="text.secondary" sx={{ fontSize: 14, fontWeight: 700 }}>
            {label}
          </Typography>
          <Typography sx={{ fontSize: { xs: 28, md: 34 }, fontWeight: 800, mt: 1 }}>
            {value}
          </Typography>
          {hint ? (
            <Typography color="text.secondary" sx={{ mt: 1 }}>
              {hint}
            </Typography>
          ) : null}
        </Box>
        <Box
          sx={{
            alignItems: 'center',
            backgroundColor: alpha(resolvedAccent, 0.14),
            borderRadius: 999,
            color: resolvedAccent,
            display: 'inline-flex',
            height: 40,
            justifyContent: 'center',
            width: 40,
          }}
        >
          <TrendingUpRoundedIcon fontSize="small" />
        </Box>
      </Stack>
    </Paper>
  )
}
