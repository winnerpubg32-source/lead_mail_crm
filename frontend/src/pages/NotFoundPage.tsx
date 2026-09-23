import { Compass } from 'lucide-react';
import { Link } from 'react-router-dom';

import { EmptyState } from '@/components/feedback/EmptyState';
import { PageHeader } from '@/components/layout/PageHeader';
import { buttonVariants } from '@/components/ui/button-variants';
import { useDocumentTitle } from '@/hooks/useDocumentTitle';
import { paths } from '@/routes/paths';

export function NotFoundPage() {
  useDocumentTitle('Page not found');

  return (
    <div>
      <PageHeader
        eyebrow="404"
        title="Page not found"
        description="The page you were looking for does not exist in this build."
      />
      <EmptyState
        icon={<Compass />}
        title="Nothing here"
        description="Check the sidebar — every module available in Phase 1 is listed there."
        action={
          <Link to={paths.dashboard} className={buttonVariants({ variant: 'primary', size: 'sm' })}>
            Back to dashboard
          </Link>
        }
        className="py-16"
      />
    </div>
  );
}
