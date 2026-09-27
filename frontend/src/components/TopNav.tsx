import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { useAuth } from "../lib/auth";
import { Icon } from "./Icon";
import { LoginModal } from "./LoginModal";

/** Black band: brand lockup left, identity and the log in / log out button right. */
export function TopNav({ showPortalLink = false }: { showPortalLink?: boolean }) {
  const { state, signOut } = useAuth();
  const navigate = useNavigate();
  const [loginOpen, setLoginOpen] = useState(false);

  const logOut = async () => {
    await signOut();
    navigate("/");
  };

  return (
    <header className="topnav">
      <Link to="/" className="brand" aria-label="FIRM FLOW home">
        <img src="/logo.png" alt="" />
        <span className="brand-name">FIRM FLOW</span>
      </Link>

      <div className="nav-right">
        {state.status === "signed_in" ? (
          <>
            <div className="identity">
              <span className="identity-name">{state.me.full_name}</span>
              <span className="identity-meta">
                {state.me.role === "admin" ? "Admin" : "Employee"}
                {state.me.firm_name ? ` · ${state.me.firm_name}` : ""}
              </span>
            </div>
            {showPortalLink && (
              <Link to={state.me.role === "admin" ? "/admin" : "/app"} className="btn btn-primary">
                Open {state.me.role === "admin" ? "dashboard" : "onboarding"}
                <Icon name="arrowRight" />
              </Link>
            )}
            <button type="button" className="btn btn-inverse" onClick={logOut}>
              <Icon name="logout" />
              Log out
            </button>
          </>
        ) : (
          <button type="button" className="btn btn-primary" onClick={() => setLoginOpen(true)} disabled={state.status === "loading"}>
            <Icon name="login" />
            Log in
          </button>
        )}
      </div>

      {loginOpen && <LoginModal onClose={() => setLoginOpen(false)} />}
    </header>
  );
}
