import { useEffect, useMemo, useRef, useState } from 'react'
import * as d3 from 'd3'

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws/alerts'
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function PatternChart({ alerts }) {
  const ref = useRef(null)

  const data = useMemo(() => {
    const counts = new Map()
    alerts.forEach((a) => counts.set(a.pattern, (counts.get(a.pattern) || 0) + 1))
    return Array.from(counts, ([pattern, count]) => ({ pattern, count }))
  }, [alerts])

  useEffect(() => {
    const svg = d3.select(ref.current)
    svg.selectAll('*').remove()

    const width = 640
    const height = 280
    const margin = { top: 20, right: 20, bottom: 60, left: 60 }

    svg.attr('viewBox', `0 0 ${width} ${height}`)

    const x = d3.scaleBand().domain(data.map((d) => d.pattern)).range([margin.left, width - margin.right]).padding(0.2)
    const y = d3.scaleLinear().domain([0, d3.max(data, (d) => d.count) || 1]).nice().range([height - margin.bottom, margin.top])

    svg
      .append('g')
      .selectAll('rect')
      .data(data)
      .join('rect')
      .attr('x', (d) => x(d.pattern))
      .attr('y', (d) => y(d.count))
      .attr('width', x.bandwidth())
      .attr('height', (d) => y(0) - y(d.count))
      .attr('fill', '#0f766e')

    svg
      .append('g')
      .attr('transform', `translate(0,${height - margin.bottom})`)
      .call(d3.axisBottom(x))
      .selectAll('text')
      .attr('transform', 'rotate(-25)')
      .style('text-anchor', 'end')

    svg.append('g').attr('transform', `translate(${margin.left},0)`).call(d3.axisLeft(y).ticks(6))
  }, [data])

  return <svg ref={ref} className="chart" />
}

export default function App() {
  const [alerts, setAlerts] = useState([])
  const [status, setStatus] = useState('connecting')

  useEffect(() => {
    fetch(`${API_URL}/alerts?limit=100`)
      .then((r) => r.json())
      .then((rows) => setAlerts(rows || []))
      .catch(() => {})

    const ws = new WebSocket(WS_URL)
    ws.onopen = () => {
      setStatus('connected')
      ws.send('ping')
    }
    ws.onmessage = (evt) => {
      try {
        const msg = JSON.parse(evt.data)
        if (msg.type === 'alerts' && Array.isArray(msg.data)) {
          setAlerts((prev) => [...msg.data, ...prev].slice(0, 300))
        }
      } catch {
        // ignore
      }
    }
    ws.onclose = () => setStatus('closed')
    ws.onerror = () => setStatus('error')

    const timer = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) ws.send('ping')
    }, 10000)

    return () => {
      clearInterval(timer)
      ws.close()
    }
  }, [])

  return (
    <div className="page">
      <header>
        <h1>Market Abuse Surveillance</h1>
        <p>Realtime alert triage and pattern concentration</p>
        <span className={`status status-${status}`}>{status}</span>
      </header>

      <section className="panel">
        <h2>Alert Pattern Distribution</h2>
        <PatternChart alerts={alerts} />
      </section>

      <section className="panel">
        <h2>Latest Alerts</h2>
        <table>
          <thead>
            <tr>
              <th>Time</th>
              <th>Pattern</th>
              <th>Account</th>
              <th>Symbol</th>
              <th>Severity</th>
              <th>Score</th>
            </tr>
          </thead>
          <tbody>
            {alerts.slice(0, 20).map((a) => (
              <tr key={a.alert_id}>
                <td>{new Date(a.ts).toLocaleTimeString()}</td>
                <td>{a.pattern}</td>
                <td>{a.account_id}</td>
                <td>{a.symbol}</td>
                <td>{a.severity}</td>
                <td>{a.score?.toFixed?.(3) ?? a.score}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  )
}
