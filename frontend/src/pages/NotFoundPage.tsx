import { Link } from 'react-router-dom'
import { Compass } from 'lucide-react'
import { Button, Card, EmptyState } from '../components/ui'

export function NotFoundPage() {
  return (
    <Card>
      <EmptyState
        icon={<Compass size={26} />}
        title="Page not found"
        description="The page you were looking for does not exist in SocialScope AI."
        action={
          <div className="mt-2 flex flex-wrap justify-center gap-2.5">
            <Link to="/dashboard">
              <Button>Back to dashboard</Button>
            </Link>
            <Link to="/">
              <Button variant="secondary">Go to home</Button>
            </Link>
          </div>
        }
      />
    </Card>
  )
}
