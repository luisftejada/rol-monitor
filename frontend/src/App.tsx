import { Route, Routes } from "react-router-dom";

import { Layout } from "@/components/Layout";
import { CharacterListPage } from "@/pages/CharacterListPage";
import { CharacterPage } from "@/pages/CharacterPage";

export function App(): React.JSX.Element {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<CharacterListPage />} />
        <Route path="characters/:id" element={<CharacterPage />} />
      </Route>
    </Routes>
  );
}
