import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import ARTargetPrecision from './ARTargetPrecision';

vi.mock('@/hooks/useBilling', () => ({
  useBilling: () => ({
    canUse: () => false
  })
}));

describe('ARTargetPrecision', () => {
  it('shows the upgrade CTA when locked', () => {
    render(
      <MemoryRouter>
        <ARTargetPrecision />
      </MemoryRouter>
    );

    const link = screen.getByRole('link', { name: /unlock with socceriq pro/i });
    expect(screen.getByText(/AR Target precision scoring is a Pro feature/i)).toBeInTheDocument();
    expect(link.closest('div')).toMatchInlineSnapshot(`
      <div
        class="alert"
      >
        🔒
        AR Target precision scoring is a Pro feature.
        <a
          class="link"
          href="/upgrade"
        >
          Unlock with SoccerIQ Pro
        </a>
      </div>
    `);
  });
});
