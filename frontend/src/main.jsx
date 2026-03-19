import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import { MantineProvider, createTheme } from '@mantine/core'
import '@mantine/core/styles.css';

const theme = createTheme({
  black: "#16161D"
})

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
    <MantineProvider theme={theme}>
      <App />
    </MantineProvider>
);
