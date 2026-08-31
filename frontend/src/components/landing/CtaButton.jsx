import { Link } from "react-router-dom";

const VARIANT_CLASSES = {
  solid:
    "bg-[var(--primary)] text-[var(--surface)] hover:bg-[var(--primary-light)]",
  outline:
    "border border-[var(--sky)] text-[var(--sky)] hover:bg-[var(--primary-light)]",
  "outline-primary":
    "border border-[var(--primary)] text-[var(--primary)] hover:bg-[var(--surface-warm)]",
};

function CtaButton({ to, href, variant = "solid", icon: Icon, children }) {
  const className = `inline-flex items-center gap-1.5 rounded-md px-4 py-2.5 text-sm font-medium transition-colors ${VARIANT_CLASSES[variant]}`;

  if (href) {
    return (
      <a href={href} className={className}>
        {Icon && <Icon className="h-4 w-4" />}
        {children}
      </a>
    );
  }

  return (
    <Link to={to} className={className}>
      {Icon && <Icon className="h-4 w-4" />}
      {children}
    </Link>
  );
}

export default CtaButton;
