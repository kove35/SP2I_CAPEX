// NOTE: le decoupage `manualChunks` a ete RETIRE.
// Cause : il produisait un bundle de production casse (erreur TDZ
// "Cannot access 'Sc' before initialization") -> React ne montait pas (ecran vide).
// Ne pas reintroduire de decoupage manuel sans un post-build smoke vert
// (`npm run test:postbuild`).
export default {};

