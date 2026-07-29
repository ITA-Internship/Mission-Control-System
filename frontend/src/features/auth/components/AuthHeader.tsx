import { MissionControlLogo } from "./MissionControlLogo";

export function AuthHeader() {
  return (
    <header className="flex flex-col items-center gap-3 border-b border-white/[0.06] px-8 pt-8 pb-6">
      <MissionControlLogo className="text-mc-accent" />

      <div className="flex flex-col items-center gap-0.5">
        <span className="text-xs font-semibold tracking-[0.2em] text-mc-accent uppercase">
          Mission Control System
        </span>

        <span className="font-mono text-[11px] tracking-wider text-mc-subtle uppercase">
          Drone Fleet Management
        </span>
      </div>
    </header>
  );
}