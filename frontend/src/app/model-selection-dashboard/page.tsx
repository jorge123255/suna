"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer } from 'recharts'

// Define types for our API responses
interface ModelSelectionStats {
  total_selections: number
  models_used: Record<string, number>
  task_types: Record<string, number>
  confidence_avg: number
  override_rate: number
}

interface ModelSelection {
  id: string
  timestamp: string
  prompt_preview: string
  prompt_length: number
  task_type: string
  confidence: number
  selected_model: string
  override_reason: string | null
}

interface StatsResponse {
  source: string
  stats: ModelSelectionStats
  message?: string
  error?: string
}

interface RecentResponse {
  source: string
  selections: ModelSelection[]
  message?: string
  error?: string
}

// Define colors for charts
const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d'];

export default function ModelSelectionDashboard() {
  const [stats, setStats] = useState<ModelSelectionStats | null>(null)
  const [recent, setRecent] = useState<ModelSelection[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true)
      try {
        // Fetch stats
        const statsResponse = await fetch('/api/model-selection/stats')
        const statsData: StatsResponse = await statsResponse.json()
        
        if (statsData.error) {
          setError(statsData.error)
        } else {
          setStats(statsData.stats)
        }
        
        // Fetch recent selections
        const recentResponse = await fetch('/api/model-selection/recent')
        const recentData: RecentResponse = await recentResponse.json()
        
        if (recentData.error) {
          setError(recentData.error)
        } else {
          setRecent(recentData.selections)
        }
      } catch (err) {
        setError('Failed to fetch data. Please try again later.')
        console.error(err)
      } finally {
        setLoading(false)
      }
    }
    
    fetchData()
  }, [])

  // Transform data for charts
  const getModelData = () => {
    if (!stats) return []
    return Object.entries(stats.models_used).map(([name, value]) => ({
      name,
      value
    }))
  }
  
  const getTaskData = () => {
    if (!stats) return []
    return Object.entries(stats.task_types).map(([name, value]) => ({
      name,
      value
    }))
  }

  return (
    <div className="container mx-auto py-10">
      <h1 className="text-3xl font-bold mb-6">Model Selection Dashboard</h1>
      
      {loading ? (
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
        </div>
      ) : error ? (
        <Card>
          <CardContent className="pt-6">
            <div className="text-center text-destructive">
              <p>{error}</p>
              <p className="mt-2">This could be because no model selections have been logged yet.</p>
            </div>
          </CardContent>
        </Card>
      ) : (
        <Tabs defaultValue="overview">
          <TabsList className="mb-4">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="recent">Recent Selections</TabsTrigger>
          </TabsList>
          
          <TabsContent value="overview">
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium">Total Selections</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{stats?.total_selections || 0}</div>
                </CardContent>
              </Card>
              
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium">Avg. Confidence</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{stats?.confidence_avg.toFixed(2) || 0}</div>
                </CardContent>
              </Card>
              
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium">Override Rate</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{stats?.override_rate.toFixed(1) || 0}%</div>
                </CardContent>
              </Card>
              
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium">Models Used</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{Object.keys(stats?.models_used || {}).length}</div>
                </CardContent>
              </Card>
            </div>
            
            <div className="grid gap-4 md:grid-cols-2 mt-4">
              <Card>
                <CardHeader>
                  <CardTitle>Models Distribution</CardTitle>
                  <CardDescription>Distribution of models used for queries</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="h-80">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={getModelData()}
                          cx="50%"
                          cy="50%"
                          labelLine={true}
                          label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                          outerRadius={80}
                          fill="#8884d8"
                          dataKey="value"
                        >
                          {getModelData().map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                          ))}
                        </Pie>
                        <Tooltip />
                        <Legend />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                </CardContent>
              </Card>
              
              <Card>
                <CardHeader>
                  <CardTitle>Task Types</CardTitle>
                  <CardDescription>Distribution of task types</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="h-80">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart
                        data={getTaskData()}
                        margin={{
                          top: 5,
                          right: 30,
                          left: 20,
                          bottom: 5,
                        }}
                      >
                        <XAxis dataKey="name" />
                        <YAxis />
                        <Tooltip />
                        <Legend />
                        <Bar dataKey="value" fill="#8884d8">
                          {getTaskData().map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
          
          <TabsContent value="recent">
            <Card>
              <CardHeader>
                <CardTitle>Recent Model Selections</CardTitle>
                <CardDescription>The most recent model selection decisions</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left py-3 px-4">Time</th>
                        <th className="text-left py-3 px-4">Prompt</th>
                        <th className="text-left py-3 px-4">Task Type</th>
                        <th className="text-left py-3 px-4">Confidence</th>
                        <th className="text-left py-3 px-4">Model</th>
                        <th className="text-left py-3 px-4">Override</th>
                      </tr>
                    </thead>
                    <tbody>
                      {recent.length === 0 ? (
                        <tr>
                          <td colSpan={6} className="text-center py-4">No recent selections found</td>
                        </tr>
                      ) : (
                        recent.map((selection) => (
                          <tr key={selection.id} className="border-b hover:bg-muted/50">
                            <td className="py-3 px-4">{new Date(selection.timestamp).toLocaleString()}</td>
                            <td className="py-3 px-4 max-w-xs truncate">{selection.prompt_preview}</td>
                            <td className="py-3 px-4">{selection.task_type}</td>
                            <td className="py-3 px-4">{selection.confidence.toFixed(2)}</td>
                            <td className="py-3 px-4">{selection.selected_model}</td>
                            <td className="py-3 px-4">
                              {selection.override_reason ? (
                                <span className="text-amber-500" title={selection.override_reason}>Yes</span>
                              ) : (
                                <span className="text-green-500">No</span>
                              )}
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      )}
    </div>
  )
}
