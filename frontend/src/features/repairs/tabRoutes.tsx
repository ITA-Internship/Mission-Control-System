import { useOutletContext } from "react-router";

import { DefectsTab } from "./tabs/DefectsTab";
import { OrdersTab } from "./tabs/OrdersTab";
import { ReplacementsTab } from "./tabs/ReplacementsTab";

import type { RepairsOutletContext } from "./pages/RepairsPage";

function useRepairsTabProps() {
  const {
    reloadSignal,
    onNetworkStateChange,
    onDataChanged,
  } = useOutletContext<RepairsOutletContext>();

  return {
    reloadSignal,
    onNetworkStateChange,
    onDataChanged,
  };
}

export function DefectsRoute() {
  const props = useRepairsTabProps();
  return <DefectsTab {...props} />;
}

export function OrdersRoute() {
  const props = useRepairsTabProps();
  return <OrdersTab {...props} />;
}

export function ReplacementsRoute() {
  const props = useRepairsTabProps();
  return <ReplacementsTab {...props} />;
}
