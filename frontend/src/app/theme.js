import { alpha, createTheme } from '@mui/material/styles'

const primaryMain = '#1d7565'
const secondaryMain = '#cb7a33'
const sidebarMain = '#102228'

export const appTheme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: primaryMain,
      dark: '#125547',
      light: '#4d9f91',
      contrastText: '#f6fbf9',
    },
    secondary: {
      main: secondaryMain,
      dark: '#9a5820',
      light: '#e3a066',
      contrastText: '#fffaf5',
    },
    error: {
      main: '#b24b47',
    },
    warning: {
      main: '#c68d2f',
    },
    success: {
      main: '#2d8d67',
    },
    text: {
      primary: '#132125',
      secondary: '#5e6d72',
    },
    background: {
      default: '#eef2ef',
      paper: '#fbfcfa',
    },
    divider: alpha('#15323a', 0.1),
  },
  shape: {
    borderRadius: 20,
  },
  typography: {
    fontFamily: '"Manrope", sans-serif',
    h1: {
      fontSize: '3rem',
      fontWeight: 700,
      letterSpacing: '-0.06em',
    },
    h2: {
      fontSize: '2rem',
      fontWeight: 700,
      letterSpacing: '-0.04em',
    },
    h3: {
      fontSize: '1.4rem',
      fontWeight: 700,
      letterSpacing: '-0.03em',
    },
    h4: {
      fontSize: '1.1rem',
      fontWeight: 700,
      letterSpacing: '-0.02em',
    },
    button: {
      fontWeight: 700,
      textTransform: 'none',
    },
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 999,
          paddingInline: 18,
          minHeight: 42,
          boxShadow: 'none',
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
          boxShadow: `0 20px 50px ${alpha(sidebarMain, 0.08)}`,
        },
      },
    },
    MuiOutlinedInput: {
      styleOverrides: {
        root: {
          borderRadius: 16,
          backgroundColor: alpha('#ffffff', 0.72),
        },
      },
    },
    MuiDrawer: {
      styleOverrides: {
        paper: {
          backgroundColor: sidebarMain,
          color: '#e7f3f0',
          borderRight: 'none',
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          fontWeight: 700,
          borderRadius: 999,
        },
      },
    },
  },
})
