import { useState } from 'react'
import {
  Box,
  Tabs,
  Tab,
  Card,
  CardContent,
  Typography,
} from '@mui/material'

function TabPanel({ children, value, index }) {
  return value === index ? <Box sx={{ p: 3 }}>{children}</Box> : null
}

export default function Admin() {
  const [tab, setTab] = useState(0)

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Admin Panel
      </Typography>

      <Card>
        <Tabs value={tab} onChange={(e, v) => setTab(v)}>
          <Tab label="Users" />
          <Tab label="System Logs" />
          <Tab label="Reindex" />
        </Tabs>

        <TabPanel value={tab} index={0}>
          <Typography>User Management - Coming soon</Typography>
        </TabPanel>

        <TabPanel value={tab} index={1}>
          <Typography>System Logs - Coming soon</Typography>
        </TabPanel>

        <TabPanel value={tab} index={2}>
          <Typography>Reindex Database - Coming soon</Typography>
        </TabPanel>
      </Card>
    </Box>
  )
}
