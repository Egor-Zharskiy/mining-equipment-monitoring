import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Typography,
} from '@mui/material'

export function ConfirmDialog({
  open,
  title,
  description,
  confirmLabel = 'Подтвердить',
  cancelLabel = 'Отмена',
  confirmColor = 'primary',
  isSubmitting = false,
  onCancel,
  onConfirm,
}) {
  return (
    <Dialog fullWidth maxWidth="xs" onClose={() => !isSubmitting && onCancel?.()} open={open}>
      <DialogTitle>{title}</DialogTitle>
      <DialogContent>
        <Typography color="text.secondary">{description}</Typography>
      </DialogContent>
      <DialogActions sx={{ px: 3, pb: 3 }}>
        <Button disabled={isSubmitting} onClick={onCancel}>
          {cancelLabel}
        </Button>
        <Button color={confirmColor} disabled={isSubmitting} onClick={onConfirm} variant="contained">
          {confirmLabel}
        </Button>
      </DialogActions>
    </Dialog>
  )
}
