import InboxRoundedIcon from '@mui/icons-material/InboxRounded'
import { Box, Button, Paper, Typography } from '@mui/material'

export function EmptyState({
  title,
  description,
  actionLabel,
  onAction,
  icon,
}) {
  return (
    <Paper
      sx={{
        alignItems: 'center',
        border: '1px dashed',
        borderColor: 'divider',
        display: 'flex',
        flexDirection: 'column',
        gap: 1.5,
        justifyContent: 'center',
        minHeight: 220,
        p: 4,
        textAlign: 'center',
      }}
    >
      <Box
        sx={{
          alignItems: 'center',
          bgcolor: 'background.default',
          borderRadius: '50%',
          display: 'inline-flex',
          height: 56,
          justifyContent: 'center',
          width: 56,
        }}
      >
        {icon ?? <InboxRoundedIcon color="primary" />}
      </Box>
      <Typography variant="h4">{title}</Typography>
      <Typography color="text.secondary" sx={{ maxWidth: 460 }}>
        {description}
      </Typography>
      {actionLabel && onAction ? (
        <Button onClick={onAction} variant="outlined">
          {actionLabel}
        </Button>
      ) : null}
    </Paper>
  )
}
