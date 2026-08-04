import type { Drone } from "../types";
import { ClassPill } from "./ClassPill";
import { StatusBadge } from "./StatusBadge";
import { X } from "lucide-react";

interface CompareModalProps {
  drones: Drone[];
  onClose: () => void;
}

export function CompareModal({ drones, onClose }: CompareModalProps) {
  const fields: { label: string; key: keyof Drone; formatter?: (val: any) => string }[] = [
    { label: "Status", key: "status" },
    { label: "Classification", key: "classification" },
    { label: "Model", key: "drone_model_name" },
    { label: "Military Unit", key: "military_unit_name" },
    { label: "Max Speed (km/h)", key: "max_speed_kmh", formatter: (val) => val ? val.toString() : "–" },
    { label: "Max Range (km)", key: "max_range_km", formatter: (val) => val ? val.toString() : "–" },
    { label: "Payload (g)", key: "payload_capacity_g", formatter: (val) => val ? val.toString() : "–" },
    { label: "Acquired", key: "acquired_at" },
    { label: "Notes", key: "notes" },
  ];

  const allSame = (key: keyof Drone) => drones.every((drone) => drone[key] === drones[0][key]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={onClose}>
      <div className="flex max-h-[85vh] w-full max-w-5xl flex-col rounded-2xl border border-white/8 bg-[#161D26] shadow-2xl" onClick={(event) => event.stopPropagation()}>
        <div className="flex shrink-0 items-center justify-between border-b border-white/8 px-6 py-4">
          <h2 className="text-[15px] font-semibold text-[#E6EAF0]">Compare Drones</h2>
          <button onClick={onClose} className="rounded p-1 text-[#8A94A6] transition-colors hover:text-[#E6EAF0]">
            <X size={16} />
          </button>
        </div>

        <div className="flex-1 overflow-auto">
          <table className="w-full text-[13px]">
            <thead>
              <tr className="border-b border-white/8">
                <th className="sticky left-0 w-36 bg-[#161D26] px-5 py-3 text-left text-[11px] font-medium uppercase tracking-wider text-[#8A94A6]">
                  Specification
                </th>
                {drones.map((drone) => (
                  <th key={drone.id} className="px-5 py-3 text-left">
                    <div className="font-semibold text-[#E6EAF0]">{drone.name}</div>
                    <div className="mt-0.5 font-mono text-[11px] text-[#8A94A6]">{drone.serial_number}</div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {fields.map((field) => {
                const same = allSame(field.key);
                return (
                  <tr key={field.key} className={`border-b border-white/5 ${same ? "" : "bg-[#C8A24A]/4"}`}>
                    <td className="sticky left-0 bg-inherit px-5 py-3 text-[11px] font-medium uppercase tracking-wider text-[#8A94A6]">
                      {field.label}
                    </td>
                    {drones.map((drone) => (
                      <td key={drone.id} className={`px-5 py-3 ${same ? "text-[#E6EAF0]" : "font-medium text-[#C8A24A]"}`}>
                        {field.key === "status" ? (
                          <StatusBadge status={drone.status} />
                        ) : field.key === "classification" ? (
                          <ClassPill c={drone.classification} />
                        ) : field.formatter ? (
                          field.formatter(drone[field.key])
                        ) : (
                          String(drone[field.key] || "-")
                        )}
                      </td>
                    ))}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        <div className="shrink-0 border-t border-white/8 px-6 py-4">
          <p className="text-[11px] text-[#8A94A6]">
            <span className="font-medium text-[#C8A24A]">Highlighted rows</span> indicate differing values across selected drones.
          </p>
        </div>
      </div>
    </div>
  );
}