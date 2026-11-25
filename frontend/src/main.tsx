import { useEffect, useState } from 'react'
import { createRoot } from 'react-dom/client'
import './styles.css'

type Connection =
  | { state: 'checking' | 'database-unavailable' | 'api-unavailable' }
  | { state: 'ready'; shop: string }

function readShopName(data: unknown): string {
  if (
    typeof data === 'object' && data !== null &&
    'status' in data && data.status === 'ok' &&
    'database' in data && data.database === 'ready' &&
    'shop_name' in data && typeof data.shop_name === 'string'
  ) {
    return data.shop_name
  }
  throw new Error('Invalid readiness response')
}

function App() {
  const [connection, setConnection] = useState<Connection>({ state: 'checking' })
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    const controller = new AbortController()
    const timeout = window.setTimeout(() => controller.abort(), 5000)
    let active = true

    async function checkHealth() {
      try {
        const response = await fetch('/api/health', { signal: controller.signal, cache: 'no-store' })
        if (response.status === 503) {
          if (active) setConnection({ state: 'database-unavailable' })
          return
        }
        if (!response.ok) throw new Error('Readiness check failed')
        const shop = readShopName(await response.json())
        if (active) setConnection({ state: 'ready', shop })
      } catch {
        if (active) setConnection({ state: 'api-unavailable' })
      } finally {
        window.clearTimeout(timeout)
      }
    }

    void checkHealth()
    return () => {
      active = false
      window.clearTimeout(timeout)
      controller.abort()
    }
  }, [attempt])

  const status = {
    checking: 'Đang kiểm tra kết nối…',
    ready: 'Ứng dụng và cơ sở dữ liệu đã sẵn sàng.',
    'database-unavailable': 'Cơ sở dữ liệu SQLite chưa sẵn sàng.',
    'api-unavailable': 'Không thể kiểm tra trạng thái qua API. Hãy thử lại.',
  }[connection.state]
  const statusColor = connection.state.endsWith('-unavailable') ? 'unavailable' : connection.state

  return (
    <>
      <header className="topbar">
        <div className="topbar-inner">
          <span className="mark" aria-hidden="true">J</span>
          <span>June OMS</span>
        </div>
      </header>
      <main>
        <h1>Trạng thái hệ thống</h1>
        <section className="panel" aria-label="Kết nối local">
          <div role="status" className="status" data-state={statusColor}>
            <span className="dot" aria-hidden="true" />
            {status}
          </div>
          {connection.state === 'ready' && (
            <dl>
              <div><dt>Cửa hàng</dt><dd>{connection.shop}</dd></div>
              <div><dt>Cơ sở dữ liệu</dt><dd>SQLite</dd></div>
            </dl>
          )}
          <button
            type="button"
            disabled={connection.state === 'checking'}
            onClick={() => {
              setConnection({ state: 'checking' })
              setAttempt((value) => value + 1)
            }}
          >Kiểm tra lại</button>
        </section>
      </main>
    </>
  )
}

createRoot(document.getElementById('root')!).render(<App />)
