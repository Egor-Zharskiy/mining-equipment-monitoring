import { Box, Paper, Stack, Typography } from '@mui/material'

export function SectionCard({ title, subtitle, action, children, sx }) {
  return (
    <Paper
      sx={{
        border: '1px solid',
        borderColor: 'divider',
        minWidth: 0,
        p: { xs: 2, md: 3 },
        ...sx,
      }}
    >
      {(title || subtitle || action) && (
        <Stack
          direction={{ xs: 'column', sm: 'row' }}
          spacing={1.5}
          sx={{ alignItems: { sm: 'center' }, justifyContent: 'space-between', mb: 2.5 }}
        >
          <Box>
            {title ? <Typography variant="h4">{title}</Typography> : null}
            {subtitle ? (
              <Typography color="text.secondary" sx={{ mt: 0.5 }}>
                {subtitle}
              </Typography>
            ) : null}
          </Box>
          {action ? <Box>{action}</Box> : null}
        </Stack>
      )}
      {children}
    </Paper>
  )
}
