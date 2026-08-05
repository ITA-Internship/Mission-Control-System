import {
  CheckSquare,
  Square,
  MoreHorizontal,
  Eye,
  Pencil,
  GitCompare,
  AlertTriangle,
} from "lucide-react";
import { ClassPill } from "./ClassPill";
import { StatusBadge } from "./StatusBadge";
import type { Drone } from "../types";

interface DroneRowProps {
  drone: Drone;
  isSelected: boolean;
  isEven: boolean;
  activeKebab: string | number | null;
  onToggleSelect: (id: string | number) => void;
  onToggleKebab: (id: string | number) => void;
  onEdit: (drone: Drone) => void;
  onCompare: (drone: Drone) => void;
  onWriteOff: (drone: Drone) => void;
}

export function DroneRow({
  drone,
  isSelected,
  isEven,
  activeKebab,
  onToggleSelect,
  onToggleKebab,
  onEdit,
  onCompare,
  onWriteOff,
}: DroneRowProps) {
  const handleRowClick = () => onToggleSelect(drone.id);

  const handleSelectClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    onToggleSelect(drone.id);
  };

  const handleKebabClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    onToggleKebab(drone.id);
  };

  const menuItems = [
    { icon: Eye, label: "View" },
    {
      icon: Pencil,
      label: "Edit",
      action: () => onEdit(drone),
    },
    {
      icon: GitCompare,
      label: "Compare",
      action: () => onCompare(drone),
    },
    {
      icon: AlertTriangle,
      label: "Write-off",
      cls: "text-[#E5484D]",
      action: () => onWriteOff(drone),
    },
  ];

  return (
    <tr
      className={`group cursor-pointer border-b border-white/5 transition-colors ${
        isSelected
          ? "bg-[#C8A24A]/8 hover:bg-[#C8A24A]/10"
          : isEven
          ? "bg-transparent hover:bg-white/3"
          : "bg-[#131A22]/60 hover:bg-white/3"
      }`}
      onClick={handleRowClick}
    >
      <td className="px-3 py-[11px]" onClick={handleSelectClick}>
        <button className="text-[#8A94A6] transition-colors hover:text-[#C8A24A]">
          {isSelected ? (
            <CheckSquare size={13} className="text-[#C8A24A]" />
          ) : (
            <Square
              size={13}
              className="opacity-0 transition-opacity group-hover:opacity-100"
            />
          )}
        </button>
      </td>

      <td className="px-3 py-[11px]">
        <div className="font-mono text-[12px] text-[#E6EAF0]">
          {drone.serial_number}
        </div>
        <div className="mt-0.5 font-mono text-[10px] text-[#8A94A6]">
          {drone.inventory_number}
        </div>
      </td>

      <td className="px-3 py-[11px]">
        <span className="font-medium text-[#E6EAF0]">{drone.name}</span>
      </td>

      <td className="px-3 py-[11px]">
        <ClassPill c={drone.classification} />
      </td>

      <td className="px-3 py-[11px]">
        <StatusBadge status={drone.status as React.ComponentProps<typeof StatusBadge>["status"]} />
      </td>

      <td className="px-3 py-[11px]">
        <span className="text-[12px] tabular-nums text-[#8A94A6]">
          {drone.military_unit_name || "–"}
        </span>
      </td>

      <td className="px-3 py-[11px]" onClick={handleKebabClick}>
        <div className="relative">
          <button
            onClick={handleKebabClick}
            className="rounded-lg p-1.5 text-[#8A94A6] opacity-0 transition-all hover:bg-white/6 hover:text-[#E6EAF0] group-hover:opacity-100"
          >
            <MoreHorizontal size={14} />
          </button>

          {activeKebab === drone.id && (
            <div className="absolute right-0 top-full z-30 mt-1 min-w-[140px] rounded-xl border border-white/10 bg-[#1C2535] p-1 shadow-2xl">
              {menuItems.map((item) => (
                <button
                  key={item.label}
                  onClick={(e) => {
                    e.stopPropagation();
                    item.action?.();
                  }}
                  className={`flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-[12px] transition-colors hover:bg-white/5 ${
                    item.cls ?? "text-[#E6EAF0]"
                  }`}
                >
                  <item.icon size={12} />
                  {item.label}
                </button>
              ))}
            </div>
          )}
        </div>
      </td>
    </tr>
  );
}
