import React from "react";
import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  Video,
  FileVideo,
  UserCheck,
  Bell,
  BarChart3,
  Settings,
  Info,
} from "lucide-react";

export default function Sidebar() {
  const links = [
    { to: "/", label: "Dashboard", icon: LayoutDashboard },
    { to: "/live", label: "Live Analysis", icon: Video },
    { to: "/video-analysis", label: "Video Analysis", icon: FileVideo },
    { to: "/faces", label: "Face Recognition", icon: UserCheck },
    { to: "/events", label: "Events", icon: Bell },
    { to: "/analytics", label: "Analytics", icon: BarChart3 },
    { to: "/settings", label: "Settings", icon: Settings },
    { to: "/about", label: "About Project", icon: Info },
  ];

  return (
    <aside className="sidebar">
      <nav className="sidebar-nav">
        {links.map((link) => {
          const Icon = link.icon;
          return (
            <NavLink
              key={link.to}
              to={link.to}
              className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`}
            >
              <Icon size={18} />
              <span>{link.label}</span>
            </NavLink>
          );
        })}
      </nav>
    </aside>
  );
}
