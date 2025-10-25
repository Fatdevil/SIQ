import { Link } from 'react-router-dom';

type UpgradeCTAProps = {
  feature: string;
};

export default function UpgradeCTA({ feature }: UpgradeCTAProps) {
  return (
    <div className="alert">
      🔒 {feature} is a Pro feature.{' '}
      <Link to="/upgrade" className="link">
        Unlock with SoccerIQ Pro or Elite
      </Link>
    </div>
  );
}
