import { Route, Routes } from "react-router-dom";

import { Layout } from "@/components/Layout";
import { CharacterListPage } from "@/pages/CharacterListPage";
import { CharacterPage } from "@/pages/CharacterPage";
import { CreateCharacterPage } from "@/pages/CreateCharacterPage";
import { EditCharacterPage } from "@/pages/EditCharacterPage";

export function App(): React.JSX.Element {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<CharacterListPage />} />
        <Route path="new" element={<CreateCharacterPage />} />
        <Route path="characters/:id" element={<CharacterPage />} />
        <Route path="characters/:id/edit" element={<EditCharacterPage />} />
      </Route>
    </Routes>
  );
}
