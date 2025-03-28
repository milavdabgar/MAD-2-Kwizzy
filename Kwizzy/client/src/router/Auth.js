import LandingPage from "../views/LandingPage.vue";
import Login from "../views/Login.vue";
import Signup from "../views/Signup.vue";
const PageNotFound = () => import("../views/404.vue");
const PrivacyPolicy = () => import("../views/PrivacyPolicy.vue");
const TermsOfService = () => import("../views/TermsOfService.vue");
const ForgotPassword = () => import("../views/ForgotPassword.vue");
const ResetPassword = () => import("../views/ResetPassword.vue");

const AuthRoutes = [
  {
    path: "/",
    name: "LandingPage",
    component: LandingPage,
    meta: { title: "Kwizzy" },
  },
  {
    path: "/login",
    name: "Login",
    component: Login,
    meta: { title: "Login" },
  },
  {
    path: "/signup",
    name: "Signup",
    component: Signup,
    meta: { title: "Signup" },
  },
  {
    path: "/privacy-policy",
    name: "PrivacyPolicy",
    component: PrivacyPolicy,
    meta: { title: "Privacy Policy" },
  },
  {
    path: "/terms-of-service",
    name: "TermsOfService",
    component: TermsOfService,
    meta: { title: "Terms of Service" },
  },
  {
    path: "/forgot-password",
    name: "ForgotPassword",
    component: ForgotPassword,
    meta: { title: "Forgot Password" },
  },
  {
    path: "/reset-password",
    name: "ResetPassword",
    component: ResetPassword,
    meta: { title: "Reset Password" },
  },
  {
    path: "/:pathMatch(.*)*",
    name: "Page Not Found",
    component: PageNotFound,
    meta: { title: "404 Page Not Found" },
  },
];

export default AuthRoutes;
