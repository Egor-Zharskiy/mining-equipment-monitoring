import { Box, Stack, Typography } from '@mui/material'

export function PageHeader({ eyebrow, title, description, actions }) {
  return (
    <Stack
      direction={{ xs: 'column', md: 'row' }}
      spacing={2}
      sx={{ alignItems: { md: 'flex-end' }, justifyContent: 'space-between' }}
    >
      <Box>
        {eyebrow ? (
          <Typography
            sx={{
              color: 'primary.main',
              fontSize: 13,
              fontWeight: 800,
              letterSpacing: '0.12em',
              mb: 1,
              textTransform: 'uppercase',
            }}
          >
            {eyebrow}
          </Typography>
        ) : null}
        <Typography variant="h2" sx={{ mb: 1 }}>
          {title}
        </Typography>
        {description ? (
          <Typography color="text.secondary" sx={{ maxWidth: 720 }}>
            {description}
          </Typography>
        ) : null}
      </Box>
      {actions ? <Box>{actions}</Box> : null}
    </Stack>
  )
}
