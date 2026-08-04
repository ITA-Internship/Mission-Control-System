import { X, AlertCircle, Loader } from "lucide-react";
import { useState } from "react";

import type { Classification, DrawerMode, Drone } from "../types";
import { CLASS_COLORS, CLASSIFICATIONS } from "../utils/constants";
import { createDrone, updateDrone } from "../api/dronesApi";

interface DroneDrawerProps {
  mode: DrawerMode;
  drone?: Drone;
  onClose: () => void;
  onSave?: (drone: Drone) => void;
}

type DroneForm = {
  serial_number: string;
  inventory_number: string;
  name: string;
  drone_model: string | number;
  classification: Classification;
  military_unit: string | number;
  acquired_at: string;
  notes: string;
};

export function DroneDrawer({ mode, drone, onClose, onSave }: DroneDrawerProps) {
  const [form, setForm] = useState<DroneForm>({
    serial_number: drone?.serial_number ?? "",
    inventory_number: drone?.inventory_number ?? "",
    name: drone?.name ?? "",
    drone_model: drone?.drone_model ?? "",
    classification: drone?.classification ?? "RECONNAISSANCE",
    military_unit: drone?.military_unit ?? "",
    acquired_at: drone?.acquired_at ?? "",
    notes: drone?.notes ?? "",
  });

  const [loading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const setField = <K extends keyof DroneForm>(key: K, value: DroneForm[K]) =>
    setForm((current) => ({ ...current, [key]: value }));

  const handleSave = async () => {
    try {
      setSaving(true);
      setError(null);

      const droneData = {
        ...form,
        drone_model: parseInt(String(form.drone_model)),
        military_unit: parseInt(String(form.military_unit)),
        spec: {
          frame_type: "N/A",
          motor_model: "N/A",
          battery_type: "N/A",
          battery_capacity_mah: 0,
          camera_model: "N/A",
          flight_controller: "N/A",
          max_speed_kmh: 0.0,
          max_range_km: 0.0,
          max_flight_time_min: 0.0,
          frequency_mhz: 0,
        },
      };

      let result: Drone;
      if (mode === "add") {
        result = await createDrone(droneData);
      } else if (drone) {
        result = await updateDrone(drone.id, droneData);
      } else {
        throw new Error("No drone ID for edit mode");
      }

      onSave?.(result);
      onClose();
    } catch (err) {
      console.error(err);

      let errorMessage = "An error occurred during save.";

      const apiErr = err as { name?: string; body?: string | Record<string, string | string[]> };

      if (apiErr?.name === "ApiError" && apiErr?.body) {
        if (typeof apiErr.body === "object") {
          const errorDetails = Object.entries(apiErr.body)
            .map(([field, messages]) => {
              const msgText = Array.isArray(messages) ? messages.join(", ") : String(messages);
              return `• ${field.toUpperCase()}: ${msgText}`;
            })
            .join("\n");

          errorMessage = errorDetails || "Invalid data submitted.";
        } else {
          errorMessage = String(apiErr.body);
        }
      } else if (err instanceof Error) {
        errorMessage = err.message;
      }

      setError(errorMessage);
    } finally {
      setSaving(false);
    }
  };

  const fields: Array<{
    label: string;
    key: "serial_number" | "inventory_number" | "name";
    mono?: boolean;
  }> = [
    { label: "Serial Number", key: "serial_number", mono: true },
    { label: "Inventory Number", key: "inventory_number", mono: true },
    { label: "Name", key: "name" },
  ];

  return (
    <div className="fixed inset-0 z-50 flex justify-end" onClick={onClose}>
      <div
        className="flex h-full w-full max-w-md flex-col border-l border-white/8 bg-[#161D26] shadow-2xl"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b border-white/8 px-6 py-4">
          <h2 className="text-[15px] font-semibold text-[#E6EAF0]">
            {mode === "add" ? "Add Drone" : "Edit Drone"}
          </h2>
          <button onClick={onClose} className="rounded p-1 text-[#8A94A6] transition-colors hover:text-[#E6EAF0]">
            <X size={16} />
          </button>
        </div>

        <div className="flex-1 space-y-4 overflow-y-auto px-6 py-5">
          {error && (
            <div className="flex items-start gap-3 rounded-lg border border-[#E5484D]/50 bg-[#E5484D]/8 p-3">
              <AlertCircle size={14} className="mt-0.5 shrink-0 text-[#E5484D]" />
              <p className="text-[12px] text-[#E5484D] whitespace-pre-wrap leading-relaxed">{error}</p>
            </div>
          )}

          {loading ? (
            <div className="flex items-center justify-center py-8">
              <Loader size={20} className="animate-spin text-[#C8A24A]" />
            </div>
          ) : (
            <>
              {fields.map((field) => (
                <div key={field.key}>
                  <label className="mb-1.5 block text-[11px] font-medium uppercase tracking-wider text-[#8A94A6]">
                    {field.label}
                  </label>
                  <input
                    value={form[field.key]}
                    onChange={(event) => setField(field.key, event.target.value)}
                    className={`w-full rounded-lg border border-white/10 bg-[#0F1620] px-3 py-2 text-[13px] text-[#E6EAF0] placeholder-[#8A94A6]/50 transition-all focus:border-[#C8A24A]/50 focus:outline-none focus:ring-1 focus:ring-[#C8A24A]/50 ${field.mono ? "font-mono" : ""}`}
                  />
                </div>
              ))}

              {/* Drone Model Input */}
              <div>
                <label className="mb-1.5 block text-[11px] font-medium uppercase tracking-wider text-[#8A94A6]">
                  Drone Model ID
                </label>
                <input
                  type="number"
                  value={form.drone_model}
                  onChange={(event) => setField("drone_model", event.target.value)}
                  placeholder="Enter model ID..."
                  className="w-full rounded-lg border border-white/10 bg-[#0F1620] px-3 py-2 text-[13px] text-[#E6EAF0] placeholder-[#8A94A6]/50 transition-all focus:border-[#C8A24A]/50 focus:outline-none focus:ring-1 focus:ring-[#C8A24A]/50"
                />
              </div>

              {/* Military Unit Input */}
              <div>
                <label className="mb-1.5 block text-[11px] font-medium uppercase tracking-wider text-[#8A94A6]">
                  Military Unit ID
                </label>
                <input
                  type="number"
                  value={form.military_unit}
                  onChange={(event) => setField("military_unit", event.target.value)}
                  placeholder="Enter unit ID..."
                  className="w-full rounded-lg border border-white/10 bg-[#0F1620] px-3 py-2 text-[13px] text-[#E6EAF0] placeholder-[#8A94A6]/50 transition-all focus:border-[#C8A24A]/50 focus:outline-none focus:ring-1 focus:ring-[#C8A24A]/50"
                />
              </div>

              <div>
                <label className="mb-1.5 block text-[11px] font-medium uppercase tracking-wider text-[#8A94A6]">
                  Classification
                </label>
                <div className="grid grid-cols-2 gap-2">
                  {CLASSIFICATIONS.map((classification) => (
                    <button
                      key={classification}
                      onClick={() => setField("classification", classification)}
                      className={`rounded-lg border px-3 py-2 text-[12px] font-medium transition-all ${
                        form.classification === classification
                          ? `${CLASS_COLORS[classification]} border-opacity-100`
                          : "border-white/10 bg-transparent text-[#8A94A6] hover:border-white/20"
                      }`}
                    >
                      {classification}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="mb-1.5 block text-[11px] font-medium uppercase tracking-wider text-[#8A94A6]">
                  Acquired Date
                </label>
                <input
                  type="date"
                  value={form.acquired_at}
                  onChange={(event) => setField("acquired_at", event.target.value)}
                  className="w-full rounded-lg border border-white/10 bg-[#0F1620] px-3 py-2 text-[13px] text-[#E6EAF0] transition-all focus:border-[#C8A24A]/50 focus:outline-none focus:ring-1 focus:ring-[#C8A24A]/50"
                />
              </div>

              <div>
                <label className="mb-1.5 block text-[11px] font-medium uppercase tracking-wider text-[#8A94A6]">
                  Notes
                </label>
                <textarea
                  value={form.notes}
                  onChange={(event) => setField("notes", event.target.value)}
                  rows={3}
                  placeholder="Operational notes, maintenance remarks..."
                  className="w-full resize-none rounded-lg border border-white/10 bg-[#0F1620] px-3 py-2 text-[13px] text-[#E6EAF0] placeholder-[#8A94A6]/40 transition-all focus:border-[#C8A24A]/50 focus:outline-none focus:ring-1 focus:ring-[#C8A24A]/50"
                />
              </div>
            </>
          )}
        </div>

        <div className="flex gap-2 border-t border-white/8 px-6 py-4">
          <button
            className="flex-1 flex items-center justify-center gap-2 rounded-lg bg-[#C8A24A] py-2 text-[13px] font-semibold text-[#0B0F14] transition-colors hover:bg-[#d4ae5c] disabled:opacity-50 disabled:cursor-not-allowed"
            onClick={handleSave}
            disabled={saving || loading}
          >
            {saving && <Loader size={14} className="animate-spin" />}
            {mode === "add" ? "Add Drone" : "Save Changes"}
          </button>
          <button
            className="rounded-lg border border-white/10 bg-white/5 px-4 py-2 text-[13px] text-[#8A94A6] transition-colors hover:bg-white/8 hover:text-[#E6EAF0]"
            onClick={onClose}
            disabled={saving}
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}