import { useState, useRef } from "react";
import {
  Search, ChevronDown, ChevronUp, ChevronsUpDown, X, Plus, Upload, Download,
  GitCompare, BookOpen, MoreHorizontal, Eye, Pencil, Trash2, AlertTriangle,
  ArrowLeft, ArrowRight, Filter, Home, Map, Settings, Users, Radio,
  FileText, BarChart3, Bell, Shield, ChevronRight, CheckSquare,
  Square, Minus, RefreshCw, AlertCircle, CheckCircle2, Clock, Archive
} from "lucide-react";

// ─── Types ────────────────────────────────────────────────────────────────────

type DroneStatus =
  | "active" | "in_mission" | "maintenance" | "damaged"
  | "lost" | "decommissioned" | "sold" | "transferred" | "written_off";

type Classification = "Recon" | "Combat" | "Transport" | "Surveillance";

type SortDir = "asc" | "desc" | null;
type SortKey = "serial" | "name" | "model" | "classification" | "status" | "unit" | "acquired";

interface Drone {
  id: string;
  serial: string;
  inventoryNo: string;
  name: string;
  model: string;
  manufacturer: string;
  classification: Classification;
  status: DroneStatus;
  unit: string;
  acquired: string;
  maxAltitude: string;
  maxSpeed: string;
  range: string;
  payload: string;
  notes: string;
}

// ─── Static data ──────────────────────────────────────────────────────────────

const STATUS_UI: Record<DroneStatus, { label: string; color: string; dot: string; icon?: React.ReactNode }> = {
  active:        { label: "Active",          color: "text-[#3FB950]", dot: "bg-[#3FB950]" },
  in_mission:    { label: "In Mission",      color: "text-[#4C8DFF]", dot: "bg-[#4C8DFF]" },
  maintenance:   { label: "Maintenance",     color: "text-[#C8A24A]", dot: "bg-[#C8A24A]" },
  damaged:       { label: "Damaged",         color: "text-[#E5484D]", dot: "bg-[#E5484D]" },
  lost:          { label: "Lost",            color: "text-[#8A94A6]", dot: "bg-[#8A94A6]" },
  decommissioned:{ label: "Decommissioned",  color: "text-[#8A94A6]", dot: "bg-[#8A94A6]" },
  sold:          { label: "Sold",            color: "text-[#8A94A6]", dot: "bg-[#8A94A6]" },
  transferred:   { label: "Transferred",     color: "text-[#8A94A6]", dot: "bg-[#8A94A6]" },
  written_off:   { label: "Written-off",     color: "text-[#8A94A6]", dot: "bg-[#8A94A6]" },
};

const CLASS_COLORS: Record<Classification, string> = {
  Recon:        "bg-[#1a2840] text-[#4C8DFF] border border-[#4C8DFF]/30",
  Combat:       "bg-[#2a1518] text-[#E5484D] border border-[#E5484D]/30",
  Transport:    "bg-[#1e2a1a] text-[#3FB950] border border-[#3FB950]/30",
  Surveillance: "bg-[#2a2010] text-[#C8A24A] border border-[#C8A24A]/30",
};

const DRONES: Drone[] = [
  { id:"1",  serial:"DRN-04891-A", inventoryNo:"INV-2024-0001", name:"Shadow Falcon I",   model:"MQ-9 Reaper",      manufacturer:"General Atomics",  classification:"Recon",        status:"active",        unit:"1st Aerial Recon Sqn",    acquired:"2022-03-14", maxAltitude:"50,000 ft", maxSpeed:"240 kn", range:"1,150 nm", payload:"3,800 lb", notes:"" },
  { id:"2",  serial:"DRN-04892-B", inventoryNo:"INV-2024-0002", name:"Iron Hawk III",     model:"RQ-4 Global Hawk", manufacturer:"Northrop Grumman", classification:"Surveillance", status:"in_mission",    unit:"5th ISR Wing",            acquired:"2021-07-22", maxAltitude:"60,000 ft", maxSpeed:"357 kn", range:"8,700 nm", payload:"3,000 lb", notes:"Deployed OIR" },
  { id:"3",  serial:"DRN-05001-C", inventoryNo:"INV-2024-0003", name:"Desert Viper II",   model:"MQ-1C Gray Eagle", manufacturer:"General Atomics",  classification:"Combat",       status:"maintenance",   unit:"3rd Combat Drone Btn",    acquired:"2020-11-05", maxAltitude:"29,000 ft", maxSpeed:"167 kn", range:"400 nm",   payload:"800 lb",   notes:"Engine overhaul Q2" },
  { id:"4",  serial:"DRN-05002-D", inventoryNo:"INV-2024-0004", name:"Thunderwing Alpha", model:"RQ-170 Sentinel",  manufacturer:"Lockheed Martin",  classification:"Recon",        status:"active",        unit:"11th Recon Group",        acquired:"2023-01-09", maxAltitude:"50,000 ft", maxSpeed:"345 kn", range:"750 nm",   payload:"1,000 lb", notes:"" },
  { id:"5",  serial:"DRN-05100-E", inventoryNo:"INV-2024-0005", name:"Cargo Mule IV",     model:"K-MAX KARGO",      manufacturer:"Kaman Aerospace",  classification:"Transport",    status:"active",        unit:"246th Logistics Sqn",     acquired:"2022-08-30", maxAltitude:"15,000 ft", maxSpeed:"80 kn",  range:"300 nm",   payload:"6,000 lb", notes:"" },
  { id:"6",  serial:"DRN-05101-F", inventoryNo:"INV-2024-0006", name:"Night Stalker VII", model:"MQ-9 Reaper",      manufacturer:"General Atomics",  classification:"Combat",       status:"damaged",       unit:"3rd Combat Drone Btn",    acquired:"2019-06-18", maxAltitude:"50,000 ft", maxSpeed:"240 kn", range:"1,150 nm", payload:"3,800 lb", notes:"Airframe damage from RTB" },
  { id:"7",  serial:"DRN-05200-G", inventoryNo:"INV-2024-0007", name:"Phantom Watcher",   model:"RQ-4 Global Hawk", manufacturer:"Northrop Grumman", classification:"Surveillance", status:"active",        unit:"5th ISR Wing",            acquired:"2023-04-12", maxAltitude:"60,000 ft", maxSpeed:"357 kn", range:"8,700 nm", payload:"3,000 lb", notes:"" },
  { id:"8",  serial:"DRN-05201-H", inventoryNo:"INV-2024-0008", name:"Arctic Scout II",   model:"ScanEagle",        manufacturer:"Boeing Insitu",    classification:"Recon",        status:"in_mission",    unit:"1st Aerial Recon Sqn",    acquired:"2021-02-28", maxAltitude:"19,500 ft", maxSpeed:"80 kn",  range:"100 nm",   payload:"40 lb",    notes:"Cold weather ops" },
  { id:"9",  serial:"DRN-05300-I", inventoryNo:"INV-2024-0009", name:"Iron Cloud IX",     model:"V-Bat",            manufacturer:"Shield AI",        classification:"Transport",    status:"lost",          unit:"246th Logistics Sqn",     acquired:"2022-10-03", maxAltitude:"15,000 ft", maxSpeed:"75 kn",  range:"60 nm",    payload:"25 lb",    notes:"Lost during exercise IRON WOLF" },
  { id:"10", serial:"DRN-05301-J", inventoryNo:"INV-2024-0010", name:"Ember Hawk VI",     model:"MQ-1C Gray Eagle", manufacturer:"General Atomics",  classification:"Combat",       status:"decommissioned",unit:"3rd Combat Drone Btn",    acquired:"2016-05-20", maxAltitude:"29,000 ft", maxSpeed:"167 kn", range:"400 nm",   payload:"800 lb",   notes:"End of service life" },
  { id:"11", serial:"DRN-05400-K", inventoryNo:"INV-2024-0011", name:"Stormrider III",    model:"MQ-9 Reaper",      manufacturer:"General Atomics",  classification:"Recon",        status:"active",        unit:"11th Recon Group",        acquired:"2023-09-01", maxAltitude:"50,000 ft", maxSpeed:"240 kn", range:"1,150 nm", payload:"3,800 lb", notes:"" },
  { id:"12", serial:"DRN-05401-L", inventoryNo:"INV-2024-0012", name:"Silent Needle I",   model:"RQ-170 Sentinel",  manufacturer:"Lockheed Martin",  classification:"Surveillance", status:"maintenance",   unit:"5th ISR Wing",            acquired:"2020-04-17", maxAltitude:"50,000 ft", maxSpeed:"345 kn", range:"750 nm",   payload:"1,000 lb", notes:"Sensor suite upgrade" },
  { id:"13", serial:"DRN-05500-M", inventoryNo:"INV-2024-0013", name:"Ironclad Reaper II",model:"MQ-9 Reaper",      manufacturer:"General Atomics",  classification:"Combat",       status:"written_off",   unit:"3rd Combat Drone Btn",    acquired:"2018-11-12", maxAltitude:"50,000 ft", maxSpeed:"240 kn", range:"1,150 nm", payload:"3,800 lb", notes:"Written off post-combat loss" },
  { id:"14", serial:"DRN-05501-N", inventoryNo:"INV-2024-0014", name:"Glacier Eye IV",    model:"RQ-4 Global Hawk", manufacturer:"Northrop Grumman", classification:"Surveillance", status:"transferred",   unit:"NATO Joint ISR",          acquired:"2020-08-25", maxAltitude:"60,000 ft", maxSpeed:"357 kn", range:"8,700 nm", payload:"3,000 lb", notes:"Transfer to NATO pool" },
  { id:"15", serial:"DRN-05600-O", inventoryNo:"INV-2024-0015", name:"Swift Cargo Alpha", model:"K-MAX KARGO",      manufacturer:"Kaman Aerospace",  classification:"Transport",    status:"active",        unit:"246th Logistics Sqn",     acquired:"2024-01-15", maxAltitude:"15,000 ft", maxSpeed:"80 kn",  range:"300 nm",   payload:"6,000 lb", notes:"" },
];

const UNITS = ["All Units", "1st Aerial Recon Sqn", "5th ISR Wing", "3rd Combat Drone Btn", "11th Recon Group", "246th Logistics Sqn", "NATO Joint ISR"];
const MODELS = ["All Models", "MQ-9 Reaper", "RQ-4 Global Hawk", "MQ-1C Gray Eagle", "RQ-170 Sentinel", "K-MAX KARGO", "ScanEagle", "V-Bat"];

const NAV_ITEMS = [
  { icon: Home,      label: "Dashboard",  active: false },
  { icon: Map,       label: "Operations", active: false },
  { icon: Radio,     label: "Fleet",      active: true  },
  { icon: BarChart3, label: "Analytics",  active: false },
  { icon: Users,     label: "Personnel",  active: false },
  { icon: FileText,  label: "Reports",    active: false },
  { icon: Settings,  label: "Settings",   active: false },
];

// ─── Utility components ───────────────────────────────────────────────────────

function StatusBadge({ status }: { status: DroneStatus }) {
  const s = STATUS_UI[status];
  return (
    <span className={`inline-flex items-center gap-1.5 text-[11px] font-medium ${s.color}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${s.dot} shrink-0`} />
      {s.label}
    </span>
  );
}

function ClassPill({ c }: { c: Classification }) {
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-medium tracking-wide ${CLASS_COLORS[c]}`}>
      {c}
    </span>
  );
}

function FilterChip({ label, onRemove }: { label: string; onRemove: () => void }) {
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-[#C8A24A]/15 border border-[#C8A24A]/30 text-[#C8A24A] text-[11px] font-medium">
      {label}
      <button onClick={onRemove} className="hover:text-white transition-colors">
        <X size={10} />
      </button>
    </span>
  );
}

function SortIcon({ dir }: { dir: SortDir }) {
  if (!dir) return <ChevronsUpDown size={12} className="text-[#8A94A6]" />;
  if (dir === "asc") return <ChevronUp size={12} className="text-[#C8A24A]" />;
  return <ChevronDown size={12} className="text-[#C8A24A]" />;
}

function SkeletonRow() {
  return (
    <tr className="border-b border-white/5 animate-pulse">
      {[...Array(9)].map((_, i) => (
        <td key={i} className="px-3 py-[11px]">
          <div className="h-3 rounded bg-white/8 w-full" style={{ opacity: 0.4 }} />
        </td>
      ))}
    </tr>
  );
}

// ─── Modals ────────────────────────────────────────────────────────────────────

type DrawerMode = "add" | "edit";

interface DrawerProps {
  mode: DrawerMode;
  drone?: Drone;
  onClose: () => void;
}

function DroneDrawer({ mode, drone, onClose }: DrawerProps) {
  const [form, setForm] = useState({
    serial: drone?.serial ?? "",
    inventoryNo: drone?.inventoryNo ?? "",
    name: drone?.name ?? "",
    model: drone?.model ?? "",
    classification: drone?.classification ?? "Recon",
    unit: drone?.unit ?? "",
    acquired: drone?.acquired ?? "",
    notes: drone?.notes ?? "",
  });

  const set = (k: string, v: string) => setForm(f => ({ ...f, [k]: v }));

  return (
    <div className="fixed inset-0 z-50 flex justify-end" onClick={onClose}>
      <div
        className="w-full max-w-md h-full bg-[#161D26] border-l border-white/8 flex flex-col shadow-2xl"
        onClick={e => e.stopPropagation()}
      >
        {/* header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/8">
          <h2 className="text-[15px] font-semibold text-[#E6EAF0]">
            {mode === "add" ? "Add Drone" : "Edit Drone"}
          </h2>
          <button onClick={onClose} className="text-[#8A94A6] hover:text-[#E6EAF0] transition-colors p-1 rounded">
            <X size={16} />
          </button>
        </div>

        {/* body */}
        <div className="flex-1 overflow-y-auto px-6 py-5 space-y-4">
          {[
            { label: "Serial Number", key: "serial", mono: true },
            { label: "Inventory Number", key: "inventoryNo", mono: true },
            { label: "Name", key: "name" },
          ].map(f => (
            <div key={f.key}>
              <label className="block text-[11px] font-medium text-[#8A94A6] uppercase tracking-wider mb-1.5">{f.label}</label>
              <input
                value={(form as Record<string, string>)[f.key]}
                onChange={e => set(f.key, e.target.value)}
                className={`w-full bg-[#0F1620] border border-white/10 rounded-lg px-3 py-2 text-[13px] text-[#E6EAF0] placeholder-[#8A94A6]/50 focus:outline-none focus:ring-1 focus:ring-[#C8A24A]/50 focus:border-[#C8A24A]/50 transition-all ${f.mono ? "font-mono" : ""}`}
              />
            </div>
          ))}

          <div>
            <label className="block text-[11px] font-medium text-[#8A94A6] uppercase tracking-wider mb-1.5">Drone Model</label>
            <select
              value={form.model}
              onChange={e => set("model", e.target.value)}
              className="w-full bg-[#0F1620] border border-white/10 rounded-lg px-3 py-2 text-[13px] text-[#E6EAF0] focus:outline-none focus:ring-1 focus:ring-[#C8A24A]/50 focus:border-[#C8A24A]/50 transition-all appearance-none"
            >
              {MODELS.slice(1).map(m => <option key={m} value={m}>{m}</option>)}
            </select>
          </div>

          <div>
            <label className="block text-[11px] font-medium text-[#8A94A6] uppercase tracking-wider mb-1.5">Classification</label>
            <div className="grid grid-cols-2 gap-2">
              {(["Recon","Combat","Transport","Surveillance"] as Classification[]).map(c => (
                <button
                  key={c}
                  onClick={() => set("classification", c)}
                  className={`px-3 py-2 rounded-lg text-[12px] font-medium border transition-all ${
                    form.classification === c
                      ? `${CLASS_COLORS[c]} border-opacity-100`
                      : "bg-transparent border-white/10 text-[#8A94A6] hover:border-white/20"
                  }`}
                >
                  {c}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-[11px] font-medium text-[#8A94A6] uppercase tracking-wider mb-1.5">Military Unit</label>
            <select
              value={form.unit}
              onChange={e => set("unit", e.target.value)}
              className="w-full bg-[#0F1620] border border-white/10 rounded-lg px-3 py-2 text-[13px] text-[#E6EAF0] focus:outline-none focus:ring-1 focus:ring-[#C8A24A]/50 focus:border-[#C8A24A]/50 transition-all appearance-none"
            >
              {UNITS.slice(1).map(u => <option key={u} value={u}>{u}</option>)}
            </select>
          </div>

          <div>
            <label className="block text-[11px] font-medium text-[#8A94A6] uppercase tracking-wider mb-1.5">Acquired Date</label>
            <input
              type="date"
              value={form.acquired}
              onChange={e => set("acquired", e.target.value)}
              className="w-full bg-[#0F1620] border border-white/10 rounded-lg px-3 py-2 text-[13px] text-[#E6EAF0] focus:outline-none focus:ring-1 focus:ring-[#C8A24A]/50 focus:border-[#C8A24A]/50 transition-all"
            />
          </div>

          <div>
            <label className="block text-[11px] font-medium text-[#8A94A6] uppercase tracking-wider mb-1.5">Notes</label>
            <textarea
              value={form.notes}
              onChange={e => set("notes", e.target.value)}
              rows={3}
              placeholder="Operational notes, maintenance remarks..."
              className="w-full bg-[#0F1620] border border-white/10 rounded-lg px-3 py-2 text-[13px] text-[#E6EAF0] placeholder-[#8A94A6]/40 focus:outline-none focus:ring-1 focus:ring-[#C8A24A]/50 focus:border-[#C8A24A]/50 transition-all resize-none"
            />
          </div>
        </div>

        {/* footer */}
        <div className="px-6 py-4 border-t border-white/8 flex gap-2">
          <button
            className="flex-1 bg-[#C8A24A] hover:bg-[#d4ae5c] text-[#0B0F14] font-semibold text-[13px] py-2 rounded-lg transition-colors"
            onClick={onClose}
          >
            {mode === "add" ? "Add Drone" : "Save Changes"}
          </button>
          <button
            className="px-4 py-2 bg-white/5 hover:bg-white/8 border border-white/10 text-[#8A94A6] hover:text-[#E6EAF0] text-[13px] rounded-lg transition-colors"
            onClick={onClose}
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}

type ImportStep = "idle" | "dragging" | "uploading" | "success" | "error";

function ImportModal({ onClose }: { onClose: () => void }) {
  const [step, setStep] = useState<ImportStep>("idle");
  const fileRef = useRef<HTMLInputElement>(null);

  const simulate = () => {
    setStep("uploading");
    setTimeout(() => setStep("success"), 1500);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={onClose}>
      <div className="bg-[#161D26] border border-white/8 rounded-2xl w-full max-w-lg shadow-2xl" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/8">
          <h2 className="text-[15px] font-semibold text-[#E6EAF0]">Import CSV</h2>
          <button onClick={onClose} className="text-[#8A94A6] hover:text-[#E6EAF0] transition-colors p-1 rounded"><X size={16} /></button>
        </div>

        <div className="px-6 py-5 space-y-4">
          {step === "idle" || step === "dragging" ? (
            <div
              onDragOver={e => { e.preventDefault(); setStep("dragging"); }}
              onDragLeave={() => setStep("idle")}
              onDrop={e => { e.preventDefault(); simulate(); }}
              onClick={() => fileRef.current?.click()}
              className={`border-2 border-dashed rounded-xl px-6 py-10 flex flex-col items-center gap-3 cursor-pointer transition-all ${
                step === "dragging"
                  ? "border-[#C8A24A]/60 bg-[#C8A24A]/5"
                  : "border-white/12 hover:border-white/20 hover:bg-white/2"
              }`}
            >
              <Upload size={28} className={step === "dragging" ? "text-[#C8A24A]" : "text-[#8A94A6]"} />
              <div className="text-center">
                <p className="text-[13px] font-medium text-[#E6EAF0]">Drop your CSV file here</p>
                <p className="text-[12px] text-[#8A94A6] mt-0.5">or click to browse</p>
              </div>
              <input ref={fileRef} type="file" accept=".csv" className="hidden" onChange={simulate} />
            </div>
          ) : step === "uploading" ? (
            <div className="border border-white/10 rounded-xl px-6 py-10 flex flex-col items-center gap-3">
              <RefreshCw size={28} className="text-[#C8A24A] animate-spin" />
              <p className="text-[13px] text-[#8A94A6]">Parsing and validating rows…</p>
            </div>
          ) : step === "success" ? (
            <div className="border border-[#3FB950]/20 bg-[#3FB950]/5 rounded-xl px-6 py-8 flex flex-col items-center gap-3">
              <CheckCircle2 size={28} className="text-[#3FB950]" />
              <div className="text-center">
                <p className="text-[13px] font-semibold text-[#E6EAF0]">Validation Complete</p>
                <p className="text-[12px] text-[#8A94A6] mt-1">14 rows OK · 1 row with errors</p>
              </div>
              <div className="w-full mt-2 bg-[#0F1620] border border-white/8 rounded-lg p-3 text-[11px] font-mono text-[#E5484D]">
                Row 8: missing required field &quot;serial&quot;
              </div>
            </div>
          ) : (
            <div className="border border-[#E5484D]/20 bg-[#E5484D]/5 rounded-xl px-6 py-10 flex flex-col items-center gap-3">
              <AlertCircle size={28} className="text-[#E5484D]" />
              <p className="text-[13px] text-[#8A94A6]">Failed to parse file. Check format and retry.</p>
            </div>
          )}

          <div className="flex items-center gap-2 text-[12px] text-[#8A94A6]">
            <FileText size={13} />
            <button className="text-[#C8A24A] hover:underline">Download CSV template</button>
          </div>
        </div>

        <div className="px-6 py-4 border-t border-white/8 flex gap-2 justify-end">
          <button onClick={onClose} className="px-4 py-2 bg-white/5 hover:bg-white/8 border border-white/10 text-[#8A94A6] text-[13px] rounded-lg transition-colors">Cancel</button>
          {step === "success" && (
            <button onClick={onClose} className="px-4 py-2 bg-[#C8A24A] hover:bg-[#d4ae5c] text-[#0B0F14] font-semibold text-[13px] rounded-lg transition-colors">
              Import 14 Drones
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

function CompareModal({ drones, onClose }: { drones: Drone[]; onClose: () => void }) {
  const fields: { label: string; key: keyof Drone }[] = [
    { label: "Status",       key: "status" },
    { label: "Classification",key:"classification" },
    { label: "Unit",         key: "unit" },
    { label: "Model",        key: "model" },
    { label: "Manufacturer", key: "manufacturer" },
    { label: "Acquired",     key: "acquired" },
    { label: "Max Altitude", key: "maxAltitude" },
    { label: "Max Speed",    key: "maxSpeed" },
    { label: "Range",        key: "range" },
    { label: "Payload",      key: "payload" },
  ];

  const allSame = (key: keyof Drone) => drones.every(d => d[key] === drones[0][key]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={onClose}>
      <div className="bg-[#161D26] border border-white/8 rounded-2xl w-full max-w-5xl max-h-[85vh] flex flex-col shadow-2xl" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/8 shrink-0">
          <h2 className="text-[15px] font-semibold text-[#E6EAF0]">Compare Drones</h2>
          <button onClick={onClose} className="text-[#8A94A6] hover:text-[#E6EAF0] transition-colors p-1 rounded"><X size={16} /></button>
        </div>

        <div className="overflow-auto flex-1">
          <table className="w-full text-[13px]">
            <thead>
              <tr className="border-b border-white/8">
                <th className="text-left px-5 py-3 text-[11px] font-medium text-[#8A94A6] uppercase tracking-wider w-36 sticky left-0 bg-[#161D26]">Specification</th>
                {drones.map(d => (
                  <th key={d.id} className="text-left px-5 py-3">
                    <div className="font-semibold text-[#E6EAF0]">{d.name}</div>
                    <div className="font-mono text-[11px] text-[#8A94A6] mt-0.5">{d.serial}</div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {fields.map(f => {
                const same = allSame(f.key);
                return (
                  <tr key={f.key} className={`border-b border-white/5 ${!same ? "bg-[#C8A24A]/4" : ""}`}>
                    <td className="px-5 py-3 text-[#8A94A6] text-[11px] uppercase tracking-wider font-medium sticky left-0 bg-inherit">{f.label}</td>
                    {drones.map(d => (
                      <td key={d.id} className={`px-5 py-3 ${!same ? "text-[#C8A24A] font-medium" : "text-[#E6EAF0]"}`}>
                        {f.key === "status"
                          ? <StatusBadge status={d.status as DroneStatus} />
                          : f.key === "classification"
                          ? <ClassPill c={d.classification} />
                          : String(d[f.key])
                        }
                      </td>
                    ))}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        <div className="px-6 py-4 border-t border-white/8 shrink-0">
          <p className="text-[11px] text-[#8A94A6]"><span className="text-[#C8A24A] font-medium">Highlighted rows</span> indicate differing values across selected drones.</p>
        </div>
      </div>
    </div>
  );
}

// ─── Main app ─────────────────────────────────────────────────────────────────

export default function App() {
  // ── Table state ──
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<DroneStatus[]>([]);
  const [classFilter, setClassFilter] = useState<Classification[]>([]);
  const [unitFilter, setUnitFilter] = useState("All Units");
  const [modelFilter, setModelFilter] = useState("All Models");
  const [sortKey, setSortKey] = useState<SortKey>("serial");
  const [sortDir, setSortDir] = useState<SortDir>("asc");
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [loading] = useState(false);

  // ── Dropdown open state ──
  const [statusOpen, setStatusOpen] = useState(false);
  const [classOpen, setClassOpen] = useState(false);
  const [activeKebab, setActiveKebab] = useState<string | null>(null);

  // ── Modals ──
  const [drawer, setDrawer] = useState<{ open: boolean; mode: DrawerMode; drone?: Drone }>({ open: false, mode: "add" });
  const [importOpen, setImportOpen] = useState(false);
  const [compareOpen, setCompareOpen] = useState(false);

  // ── Filter + sort logic ──
  const filtered = DRONES.filter(d => {
    const q = search.toLowerCase();
    const matchSearch = !q || d.serial.toLowerCase().includes(q) || d.inventoryNo.toLowerCase().includes(q) || d.name.toLowerCase().includes(q);
    const matchStatus = statusFilter.length === 0 || statusFilter.includes(d.status);
    const matchClass = classFilter.length === 0 || classFilter.includes(d.classification);
    const matchUnit = unitFilter === "All Units" || d.unit === unitFilter;
    const matchModel = modelFilter === "All Models" || d.model === modelFilter;
    return matchSearch && matchStatus && matchClass && matchUnit && matchModel;
  }).sort((a, b) => {
    if (!sortDir) return 0;
    const av = a[sortKey as keyof Drone] as string;
    const bv = b[sortKey as keyof Drone] as string;
    return sortDir === "asc" ? av.localeCompare(bv) : bv.localeCompare(av);
  });

  const total = filtered.length;
  const totalPages = Math.ceil(total / pageSize);
  const pageStart = (page - 1) * pageSize;
  const rows = filtered.slice(pageStart, pageStart + pageSize);

  const handleSort = (key: SortKey) => {
    if (sortKey !== key) { setSortKey(key); setSortDir("asc"); }
    else if (sortDir === "asc") setSortDir("desc");
    else if (sortDir === "desc") { setSortDir(null); }
    else setSortDir("asc");
  };

  const toggleSelect = (id: string) => {
    setSelected(s => {
      const n = new Set(s);
      n.has(id) ? n.delete(id) : n.add(id);
      return n;
    });
  };

  const toggleSelectAll = () => {
    if (selected.size === rows.length) setSelected(new Set());
    else setSelected(new Set(rows.map(r => r.id)));
  };

  const toggleStatus = (s: DroneStatus) => {
    setStatusFilter(f => f.includes(s) ? f.filter(x => x !== s) : [...f, s]);
    setPage(1);
  };

  const toggleClass = (c: Classification) => {
    setClassFilter(f => f.includes(c) ? f.filter(x => x !== c) : [...f, c]);
    setPage(1);
  };

  const clearAll = () => {
    setSearch(""); setStatusFilter([]); setClassFilter([]);
    setUnitFilter("All Units"); setModelFilter("All Models"); setPage(1);
  };

  const hasFilters = search || statusFilter.length || classFilter.length || unitFilter !== "All Units" || modelFilter !== "All Models";

  const selectedDrones = DRONES.filter(d => selected.has(d.id));

  const colHeader = (label: string, key: SortKey, cls = "") => (
    <th
      className={`text-left px-3 py-2.5 text-[11px] font-medium text-[#8A94A6] uppercase tracking-wider cursor-pointer hover:text-[#E6EAF0] select-none group ${cls}`}
      onClick={() => handleSort(key)}
    >
      <span className="inline-flex items-center gap-1">
        {label}
        <SortIcon dir={sortKey === key ? sortDir : null} />
      </span>
    </th>
  );

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#0B0F14]" style={{ fontFamily: "'Inter', system-ui, sans-serif" }}>
      {/* ── Sidebar ── */}
      <aside className="w-[220px] shrink-0 bg-[#0E141B] border-r border-white/6 flex flex-col">
        {/* Logo */}
        <div className="px-5 py-4 border-b border-white/6">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded bg-[#C8A24A] flex items-center justify-center">
              <Shield size={14} className="text-[#0B0F14]" />
            </div>
            <div>
              <p className="text-[13px] font-semibold text-[#E6EAF0] leading-tight">Mission</p>
              <p className="text-[10px] text-[#8A94A6] uppercase tracking-widest leading-tight">Control</p>
            </div>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-3 py-4 space-y-0.5">
          {NAV_ITEMS.map(item => (
            <button
              key={item.label}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-[13px] font-medium transition-all group ${
                item.active
                  ? "bg-[#C8A24A]/10 text-[#C8A24A] border border-[#C8A24A]/15"
                  : "text-[#8A94A6] hover:text-[#E6EAF0] hover:bg-white/4"
              }`}
            >
              <item.icon size={15} className={item.active ? "text-[#C8A24A]" : "text-[#8A94A6] group-hover:text-[#E6EAF0]"} />
              {item.label}
              {item.active && <ChevronRight size={12} className="ml-auto text-[#C8A24A]/60" />}
            </button>
          ))}
        </nav>

        {/* Sub-nav for Fleet */}
        <div className="px-3 pb-2">
          <div className="border-t border-white/6 pt-3 space-y-0.5">
            {[
              { label: "Inventory", active: true },
              { label: "Models", active: false },
              { label: "Assignments", active: false },
              { label: "Maintenance Log", active: false },
            ].map(s => (
              <button
                key={s.label}
                className={`w-full flex items-center gap-2 pl-7 pr-3 py-2 rounded-lg text-[12px] transition-all ${
                  s.active ? "text-[#C8A24A] bg-[#C8A24A]/8" : "text-[#8A94A6] hover:text-[#E6EAF0] hover:bg-white/3"
                }`}
              >
                {s.active && <span className="w-1 h-1 rounded-full bg-[#C8A24A] shrink-0" />}
                {s.label}
              </button>
            ))}
          </div>
        </div>

        {/* User */}
        <div className="border-t border-white/6 px-4 py-3 flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-full bg-[#C8A24A]/20 border border-[#C8A24A]/30 flex items-center justify-center text-[#C8A24A] text-[11px] font-semibold">JR</div>
          <div className="flex-1 min-w-0">
            <p className="text-[12px] font-medium text-[#E6EAF0] truncate">J. Rodriguez</p>
            <p className="text-[10px] text-[#8A94A6]">Fleet Admin</p>
          </div>
          <Settings size={13} className="text-[#8A94A6] hover:text-[#E6EAF0] cursor-pointer transition-colors" />
        </div>
      </aside>

      {/* ── Main ── */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top bar */}
        <header className="h-12 shrink-0 border-b border-white/6 bg-[#0E141B] flex items-center justify-between px-5">
          <div className="flex items-center gap-2 text-[12px] text-[#8A94A6]">
            <span>Fleet</span>
            <ChevronRight size={12} />
            <span className="text-[#E6EAF0]">Inventory</span>
          </div>
          <div className="flex items-center gap-3">
            <button className="relative text-[#8A94A6] hover:text-[#E6EAF0] transition-colors">
              <Bell size={15} />
              <span className="absolute -top-0.5 -right-0.5 w-1.5 h-1.5 rounded-full bg-[#E5484D]" />
            </button>
            <div className="w-px h-4 bg-white/10" />
            <span className="text-[11px] text-[#8A94A6] uppercase tracking-widest">NORTHERN COMMAND</span>
          </div>
        </header>

        {/* Content */}
        <main className="flex-1 overflow-auto">
          <div className="p-5 space-y-4">
            {/* Page header */}
            <div className="flex items-start justify-between gap-4">
              <div>
                <h1 className="text-[22px] font-semibold text-[#E6EAF0] tracking-tight">Drone Inventory</h1>
                <p className="text-[13px] text-[#8A94A6] mt-0.5">
                  <span className="text-[#C8A24A] font-semibold">{DRONES.length}</span> drones total ·{" "}
                  <span className="text-[#3FB950]">{DRONES.filter(d => d.status === "active").length} active</span> ·{" "}
                  <span className="text-[#4C8DFF]">{DRONES.filter(d => d.status === "in_mission").length} in mission</span>
                </p>
              </div>

              {/* Toolbar */}
              <div className="flex items-center gap-2 flex-wrap justify-end">
                <button
                  onClick={() => { setImportOpen(true); }}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-white/5 hover:bg-white/8 border border-white/10 text-[#8A94A6] hover:text-[#E6EAF0] text-[12px] rounded-lg transition-all"
                >
                  <Upload size={13} /> Import CSV
                </button>
                <button className="flex items-center gap-1.5 px-3 py-1.5 bg-white/5 hover:bg-white/8 border border-white/10 text-[#8A94A6] hover:text-[#E6EAF0] text-[12px] rounded-lg transition-all">
                  <Download size={13} /> Export CSV
                </button>
                <button
                  onClick={() => selected.size >= 2 && setCompareOpen(true)}
                  disabled={selected.size < 2}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-white/5 hover:bg-white/8 border border-white/10 text-[#8A94A6] hover:text-[#E6EAF0] text-[12px] rounded-lg transition-all disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  <GitCompare size={13} />
                  Compare{selected.size >= 2 ? ` (${selected.size})` : ""}
                </button>
                <button className="flex items-center gap-1.5 px-3 py-1.5 bg-white/5 hover:bg-white/8 border border-white/10 text-[#8A94A6] hover:text-[#E6EAF0] text-[12px] rounded-lg transition-all">
                  <BookOpen size={13} /> Models
                </button>
                <button
                  onClick={() => setDrawer({ open: true, mode: "add" })}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-[#C8A24A] hover:bg-[#d4ae5c] text-[#0B0F14] font-semibold text-[12px] rounded-lg transition-colors"
                >
                  <Plus size={13} /> Add Drone
                </button>
              </div>
            </div>

            {/* Filter bar */}
            <div className="bg-[#161D26] border border-white/8 rounded-xl p-3">
              <div className="flex flex-wrap items-center gap-2">
                {/* Search */}
                <div className="relative flex-1 min-w-[200px]">
                  <Search size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#8A94A6]" />
                  <input
                    value={search}
                    onChange={e => { setSearch(e.target.value); setPage(1); }}
                    placeholder="Search serial, inventory, name…"
                    className="w-full pl-8 pr-3 py-2 bg-[#0F1620] border border-white/8 rounded-lg text-[13px] text-[#E6EAF0] placeholder-[#8A94A6]/50 focus:outline-none focus:ring-1 focus:ring-[#C8A24A]/40 transition-all"
                  />
                </div>

                {/* Status dropdown */}
                <div className="relative">
                  <button
                    onClick={() => { setStatusOpen(o => !o); setClassOpen(false); }}
                    className={`flex items-center gap-1.5 px-3 py-2 rounded-lg border text-[12px] transition-all ${
                      statusFilter.length ? "border-[#C8A24A]/40 bg-[#C8A24A]/8 text-[#C8A24A]" : "border-white/10 bg-white/3 text-[#8A94A6] hover:text-[#E6EAF0]"
                    }`}
                  >
                    <Filter size={12} />
                    Status{statusFilter.length ? ` (${statusFilter.length})` : ""}
                    <ChevronDown size={11} className={statusOpen ? "rotate-180 transition-transform" : "transition-transform"} />
                  </button>
                  {statusOpen && (
                    <div className="absolute left-0 top-full mt-1 z-30 bg-[#1C2535] border border-white/10 rounded-xl shadow-2xl p-1 min-w-[180px]">
                      {(Object.entries(STATUS_UI) as [DroneStatus, typeof STATUS_UI[DroneStatus]][]).map(([key, s]) => (
                        <button
                          key={key}
                          onClick={() => toggleStatus(key)}
                          className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-[12px] hover:bg-white/5 transition-colors text-left"
                        >
                          <span className={`w-1.5 h-1.5 rounded-full ${s.dot} shrink-0`} />
                          <span className="flex-1 text-[#E6EAF0]">{s.label}</span>
                          {statusFilter.includes(key) && <CheckCircle2 size={12} className="text-[#C8A24A]" />}
                        </button>
                      ))}
                    </div>
                  )}
                </div>

                {/* Classification dropdown */}
                <div className="relative">
                  <button
                    onClick={() => { setClassOpen(o => !o); setStatusOpen(false); }}
                    className={`flex items-center gap-1.5 px-3 py-2 rounded-lg border text-[12px] transition-all ${
                      classFilter.length ? "border-[#C8A24A]/40 bg-[#C8A24A]/8 text-[#C8A24A]" : "border-white/10 bg-white/3 text-[#8A94A6] hover:text-[#E6EAF0]"
                    }`}
                  >
                    <Filter size={12} />
                    Classification{classFilter.length ? ` (${classFilter.length})` : ""}
                    <ChevronDown size={11} className={classOpen ? "rotate-180 transition-transform" : "transition-transform"} />
                  </button>
                  {classOpen && (
                    <div className="absolute left-0 top-full mt-1 z-30 bg-[#1C2535] border border-white/10 rounded-xl shadow-2xl p-1 min-w-[160px]">
                      {(["Recon","Combat","Transport","Surveillance"] as Classification[]).map(c => (
                        <button
                          key={c}
                          onClick={() => toggleClass(c)}
                          className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-[12px] hover:bg-white/5 transition-colors text-left"
                        >
                          <ClassPill c={c} />
                          <span className="flex-1" />
                          {classFilter.includes(c) && <CheckCircle2 size={12} className="text-[#C8A24A]" />}
                        </button>
                      ))}
                    </div>
                  )}
                </div>

                {/* Unit */}
                <select
                  value={unitFilter}
                  onChange={e => { setUnitFilter(e.target.value); setPage(1); }}
                  className={`px-3 py-2 rounded-lg border text-[12px] transition-all appearance-none bg-white/3 focus:outline-none focus:ring-1 focus:ring-[#C8A24A]/40 ${
                    unitFilter !== "All Units" ? "border-[#C8A24A]/40 text-[#C8A24A]" : "border-white/10 text-[#8A94A6]"
                  }`}
                >
                  {UNITS.map(u => <option key={u} value={u} className="bg-[#1C2535] text-[#E6EAF0]">{u}</option>)}
                </select>

                {/* Model */}
                <select
                  value={modelFilter}
                  onChange={e => { setModelFilter(e.target.value); setPage(1); }}
                  className={`px-3 py-2 rounded-lg border text-[12px] transition-all appearance-none bg-white/3 focus:outline-none focus:ring-1 focus:ring-[#C8A24A]/40 ${
                    modelFilter !== "All Models" ? "border-[#C8A24A]/40 text-[#C8A24A]" : "border-white/10 text-[#8A94A6]"
                  }`}
                >
                  {MODELS.map(m => <option key={m} value={m} className="bg-[#1C2535] text-[#E6EAF0]">{m}</option>)}
                </select>
              </div>

              {/* Active chips */}
              {hasFilters && (
                <div className="flex items-center flex-wrap gap-2 mt-2.5 pt-2.5 border-t border-white/5">
                  {statusFilter.map(s => (
                    <FilterChip key={s} label={STATUS_UI[s].label} onRemove={() => toggleStatus(s)} />
                  ))}
                  {classFilter.map(c => (
                    <FilterChip key={c} label={c} onRemove={() => toggleClass(c)} />
                  ))}
                  {unitFilter !== "All Units" && <FilterChip label={unitFilter} onRemove={() => setUnitFilter("All Units")} />}
                  {modelFilter !== "All Models" && <FilterChip label={modelFilter} onRemove={() => setModelFilter("All Models")} />}
                  {search && <FilterChip label={`"${search}"`} onRemove={() => setSearch("")} />}
                  <button onClick={clearAll} className="text-[11px] text-[#8A94A6] hover:text-[#E5484D] transition-colors ml-1">Clear all</button>
                </div>
              )}
            </div>

            {/* Table */}
            <div className="bg-[#161D26] border border-white/8 rounded-xl overflow-hidden">
              <div className="overflow-auto" style={{ maxHeight: "calc(100vh - 340px)" }}>
                <table className="w-full text-[13px] border-collapse">
                  <thead className="sticky top-0 z-10">
                    <tr className="bg-[#1C2535] border-b border-white/8">
                      <th className="w-9 px-3 py-2.5">
                        <button onClick={toggleSelectAll} className="text-[#8A94A6] hover:text-[#C8A24A] transition-colors">
                          {selected.size > 0 && selected.size < rows.length
                            ? <Minus size={13} />
                            : selected.size === rows.length && rows.length > 0
                            ? <CheckSquare size={13} className="text-[#C8A24A]" />
                            : <Square size={13} />
                          }
                        </button>
                      </th>
                      {colHeader("Serial / Inv #", "serial", "min-w-[160px]")}
                      {colHeader("Name", "name", "min-w-[140px]")}
                      {colHeader("Model", "model", "min-w-[160px]")}
                      {colHeader("Class", "classification", "min-w-[110px]")}
                      {colHeader("Status", "status", "min-w-[120px]")}
                      {colHeader("Unit", "unit", "min-w-[160px]")}
                      {colHeader("Acquired", "acquired", "min-w-[100px] text-right")}
                      <th className="w-10 px-3 py-2.5" />
                    </tr>
                  </thead>
                  <tbody>
                    {loading ? (
                      [...Array(8)].map((_, i) => <SkeletonRow key={i} />)
                    ) : rows.length === 0 ? (
                      <tr>
                        <td colSpan={9} className="px-6 py-16 text-center">
                          <div className="flex flex-col items-center gap-3">
                            <div className="w-12 h-12 rounded-full bg-white/4 flex items-center justify-center">
                              <Search size={20} className="text-[#8A94A6]" />
                            </div>
                            <div>
                              <p className="text-[14px] font-medium text-[#E6EAF0]">No drones match these filters</p>
                              <p className="text-[12px] text-[#8A94A6] mt-1">Try adjusting your search or filters</p>
                            </div>
                            <button onClick={clearAll} className="text-[12px] text-[#C8A24A] hover:underline">Clear all filters</button>
                          </div>
                        </td>
                      </tr>
                    ) : rows.map((drone, idx) => {
                      const isSelected = selected.has(drone.id);
                      const isEven = idx % 2 === 0;
                      return (
                        <tr
                          key={drone.id}
                          className={`border-b border-white/5 transition-colors group cursor-pointer ${
                            isSelected
                              ? "bg-[#C8A24A]/8 hover:bg-[#C8A24A]/10"
                              : isEven
                              ? "bg-transparent hover:bg-white/3"
                              : "bg-[#131A22]/60 hover:bg-white/3"
                          }`}
                          onClick={() => toggleSelect(drone.id)}
                        >
                          <td className="px-3 py-[11px]" onClick={e => { e.stopPropagation(); toggleSelect(drone.id); }}>
                            <button className="text-[#8A94A6] hover:text-[#C8A24A] transition-colors">
                              {isSelected
                                ? <CheckSquare size={13} className="text-[#C8A24A]" />
                                : <Square size={13} className="opacity-0 group-hover:opacity-100 transition-opacity" />
                              }
                            </button>
                          </td>
                          <td className="px-3 py-[11px]">
                            <div className="font-mono text-[12px] text-[#E6EAF0]">{drone.serial}</div>
                            <div className="font-mono text-[10px] text-[#8A94A6] mt-0.5">{drone.inventoryNo}</div>
                          </td>
                          <td className="px-3 py-[11px]">
                            <span className="font-medium text-[#E6EAF0]">{drone.name}</span>
                          </td>
                          <td className="px-3 py-[11px]">
                            <div className="text-[13px] text-[#E6EAF0]">{drone.model}</div>
                            <div className="text-[11px] text-[#8A94A6] mt-0.5">{drone.manufacturer}</div>
                          </td>
                          <td className="px-3 py-[11px]">
                            <ClassPill c={drone.classification} />
                          </td>
                          <td className="px-3 py-[11px]">
                            <StatusBadge status={drone.status} />
                          </td>
                          <td className="px-3 py-[11px] text-[12px] text-[#8A94A6]">{drone.unit}</td>
                          <td className="px-3 py-[11px] text-right">
                            <span className="text-[12px] text-[#8A94A6] tabular-nums">{drone.acquired}</span>
                          </td>
                          <td className="px-3 py-[11px]" onClick={e => e.stopPropagation()}>
                            <div className="relative">
                              <button
                                onClick={() => setActiveKebab(k => k === drone.id ? null : drone.id)}
                                className="p-1.5 rounded-lg text-[#8A94A6] hover:text-[#E6EAF0] hover:bg-white/6 opacity-0 group-hover:opacity-100 transition-all"
                              >
                                <MoreHorizontal size={14} />
                              </button>
                              {activeKebab === drone.id && (
                                <div className="absolute right-0 top-full mt-1 z-30 bg-[#1C2535] border border-white/10 rounded-xl shadow-2xl p-1 min-w-[140px]">
                                  {[
                                    { icon: Eye,          label: "View",      cls: "" },
                                    { icon: Pencil,       label: "Edit",      cls: "", action: () => { setDrawer({ open: true, mode: "edit", drone }); setActiveKebab(null); } },
                                    { icon: GitCompare,   label: "Compare",   cls: "" },
                                    { icon: AlertTriangle,label: "Write-off", cls: "text-[#E5484D]" },
                                  ].map(item => (
                                    <button
                                      key={item.label}
                                      onClick={item.action}
                                      className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-[12px] hover:bg-white/5 transition-colors ${item.cls || "text-[#E6EAF0]"}`}
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
                    })}
                  </tbody>
                </table>
              </div>

              {/* Pagination */}
              <div className="border-t border-white/8 px-4 py-3 flex items-center justify-between bg-[#161D26]">
                <div className="flex items-center gap-3 text-[12px] text-[#8A94A6]">
                  <span>Rows per page:</span>
                  <select
                    value={pageSize}
                    onChange={e => { setPageSize(Number(e.target.value)); setPage(1); }}
                    className="bg-[#0F1620] border border-white/10 rounded-lg px-2 py-1 text-[12px] text-[#E6EAF0] focus:outline-none focus:ring-1 focus:ring-[#C8A24A]/40"
                  >
                    {[10, 25, 50, 100].map(n => <option key={n} value={n}>{n}</option>)}
                  </select>
                </div>

                <div className="flex items-center gap-4 text-[12px]">
                  <span className="text-[#8A94A6]">
                    Showing <span className="text-[#E6EAF0] font-medium">{Math.min(pageStart + 1, total)}–{Math.min(pageStart + pageSize, total)}</span> of{" "}
                    <span className="text-[#E6EAF0] font-medium">{total}</span>
                  </span>
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => setPage(p => Math.max(1, p - 1))}
                      disabled={page === 1}
                      className="p-1.5 rounded-lg border border-white/10 text-[#8A94A6] hover:text-[#E6EAF0] hover:bg-white/5 disabled:opacity-30 disabled:cursor-not-allowed transition-all"
                    >
                      <ArrowLeft size={13} />
                    </button>
                    {[...Array(Math.min(totalPages, 7))].map((_, i) => {
                      const pg = i + 1;
                      return (
                        <button
                          key={pg}
                          onClick={() => setPage(pg)}
                          className={`w-7 h-7 rounded-lg text-[12px] font-medium transition-all ${
                            pg === page
                              ? "bg-[#C8A24A] text-[#0B0F14]"
                              : "text-[#8A94A6] hover:text-[#E6EAF0] hover:bg-white/5 border border-white/10"
                          }`}
                        >
                          {pg}
                        </button>
                      );
                    })}
                    <button
                      onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                      disabled={page === totalPages || totalPages === 0}
                      className="p-1.5 rounded-lg border border-white/10 text-[#8A94A6] hover:text-[#E6EAF0] hover:bg-white/5 disabled:opacity-30 disabled:cursor-not-allowed transition-all"
                    >
                      <ArrowRight size={13} />
                    </button>
                  </div>
                </div>
              </div>
            </div>

            {/* Status legend */}
            <div className="flex flex-wrap items-center gap-4 px-1">
              {(Object.entries(STATUS_UI) as [DroneStatus, typeof STATUS_UI[DroneStatus]][]).map(([key, s]) => (
                <span key={key} className="flex items-center gap-1.5 text-[11px] text-[#8A94A6]">
                  <span className={`w-1.5 h-1.5 rounded-full ${s.dot}`} />
                  {s.label}: <span className="text-[#E6EAF0] font-medium">{DRONES.filter(d => d.status === key).length}</span>
                </span>
              ))}
            </div>
          </div>
        </main>
      </div>

      {/* ── Overlays ── */}
      {(statusOpen || classOpen || activeKebab) && (
        <div
          className="fixed inset-0 z-20"
          onClick={() => { setStatusOpen(false); setClassOpen(false); setActiveKebab(null); }}
        />
      )}
      {drawer.open && <DroneDrawer mode={drawer.mode} drone={drawer.drone} onClose={() => setDrawer(d => ({ ...d, open: false }))} />}
      {importOpen && <ImportModal onClose={() => setImportOpen(false)} />}
      {compareOpen && selectedDrones.length >= 2 && <CompareModal drones={selectedDrones.slice(0, 4)} onClose={() => setCompareOpen(false)} />}
    </div>
  );
}
