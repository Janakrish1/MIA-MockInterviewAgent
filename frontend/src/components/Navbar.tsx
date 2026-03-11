import { Link, useLocation } from "react-router-dom";
import { Terminal } from "lucide-react";

const Navbar = () => {
  const location = useLocation();

  return (
    <nav className="fixed left-0 right-0 top-0 z-50 border-b border-border bg-background/80 backdrop-blur-xl">
      <div className="container mx-auto flex h-16 items-center justify-between px-6">
        <Link to="/" className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 glow-primary">
            <Terminal className="h-4 w-4 text-primary" />
          </div>
          <span className="text-lg font-bold text-foreground">
            MIA<span className="text-primary">.</span>
          </span>
        </Link>

        <div className="flex items-center gap-6">
          {[
            { path: "/", label: "Home" },
            { path: "/interview", label: "Interview" },
            { path: "/report", label: "Report" },
          ].map(({ path, label }) => (
            <Link
              key={path}
              to={path}
              className={`text-sm font-medium transition-colors ${
                location.pathname === path
                  ? "text-primary"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              {label}
            </Link>
          ))}
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
