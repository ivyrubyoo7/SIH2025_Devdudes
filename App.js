// AuthPage.jsx
import React, { useState, useRef } from "react";
import "bootstrap/dist/css/bootstrap.min.css";
import Swal from "sweetalert2";
import { initializeApp } from "firebase/app";
import {
  getAuth,
  createUserWithEmailAndPassword,
  signInWithEmailAndPassword,
  GoogleAuthProvider,
  signInWithPopup,
  RecaptchaVerifier,
  signInWithPhoneNumber,
} from "firebase/auth";
import { getDatabase, ref, set } from "firebase/database";

// ---------- FIREBASE CONFIG ----------
const firebaseConfig = {
  apiKey: "AIzaSyBNd1KEA7s2w-tYFfWrX3M4hyiLVmFh20Q",
  authDomain: "krishi-advisory.firebaseapp.com",
  databaseURL:
    "https://krishi-advisory-default-rtdb.asia-southeast1.firebasedatabase.app",
  projectId: "krishi-advisory",
  storageBucket: "krishi-advisory.appspot.com",
  messagingSenderId: "87620381345",
  appId: "1:87620381345:web:262b8954fc385de6c31ee0",
  measurementId: "G-V2MHJ26GFB",
};

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const db = getDatabase(app);

export default function AuthPage() {
  const [mode, setMode] = useState("signin"); // signin | signup
  const [method, setMethod] = useState("email"); // email | phone
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [rePassword, setRePassword] = useState("");
  const [phone, setPhone] = useState("");
  const [otp, setOtp] = useState("");
  const confirmationResultRef = useRef(null);

  // ------------------- EMAIL REGISTER / LOGIN -------------------
  async function handleEmailAuth(e) {
    e.preventDefault();
    try {
      if (mode === "signup") {
        if (password !== rePassword) {
          Swal.fire("Error", "Passwords do not match!", "error");
          return;
        }
        const userCred = await createUserWithEmailAndPassword(
          auth,
          email,
          password
        );
        await set(ref(db, "users/" + userCred.user.uid), {
          email: userCred.user.email,
          createdAt: new Date().toISOString(),
        });
        Swal.fire("Success", "Registered successfully!", "success");
      } else {
        const userCred = await signInWithEmailAndPassword(auth, email, password);
        Swal.fire("Welcome", `Logged in as ${userCred.user.email}`, "success");
      }
    } catch (err) {
      Swal.fire("Error", err.message, "error");
    }
  }

  // ------------------- GOOGLE LOGIN -------------------
  async function handleGoogleLogin() {
    try {
      const provider = new GoogleAuthProvider();
      const userCred = await signInWithPopup(auth, provider);
      const user = userCred.user;

      await set(ref(db, "users/" + user.uid), {
        email: user.email,
        displayName: user.displayName,
        createdAt: new Date().toISOString(),
      });

      Swal.fire("Success", `Signed in with Google: ${user.displayName}`, "success");
    } catch (err) {
      Swal.fire("Error", err.message, "error");
    }
  }

  // ------------------- PHONE OTP LOGIN -------------------
  function setupRecaptcha() {
    if (!window.recaptchaVerifier) {
      window.recaptchaVerifier = new RecaptchaVerifier(
        "recaptcha-container", // 👈 must exist in DOM
        {
          size: "invisible",
          callback: () => {
            console.log("reCAPTCHA verified");
          },
          "expired-callback": () => {
            Swal.fire("Error", "reCAPTCHA expired. Please try again.", "error");
          },
        },
        auth // 👈 correct way
      );
    }
    return window.recaptchaVerifier;
  }

  async function sendOtp(e) {
    e.preventDefault();
    if (!phone) {
      Swal.fire("Error", "Enter phone number with country code", "error");
      return;
    }
    try {
      const appVerifier = setupRecaptcha();
      console.log("AppVerifier initialized:", appVerifier);

      const confirmationResult = await signInWithPhoneNumber(
        auth,
        phone,
        appVerifier
      );
      confirmationResultRef.current = confirmationResult;
      Swal.fire("OTP Sent", "Please check your SMS for the OTP", "info");
    } catch (err) {
      console.error("OTP send error:", err);
      Swal.fire("Error", err.message, "error");
    }
  }

  async function verifyOtp(e) {
    e.preventDefault();
    if (!otp) {
      Swal.fire("Error", "Enter the OTP received", "error");
      return;
    }
    try {
      const confirmationResult = confirmationResultRef.current;
      const userCred = await confirmationResult.confirm(otp);

      await set(ref(db, "users/" + userCred.user.uid), {
        phone: userCred.user.phoneNumber,
        createdAt: new Date().toISOString(),
      });

      Swal.fire("Success", "Phone number verified & logged in!", "success");
    } catch (err) {
      Swal.fire("Error", err.message, "error");
    }
  }

  // ------------------- UI -------------------
  return (
    <div
      className="d-flex align-items-center justify-content-center vh-100"
      style={{
        background: "linear-gradient(to bottom, #FF9933, #FFFFFF, #138808)",
      }}
    >
      <div
        className="card shadow-lg p-4"
        style={{ width: "100%", maxWidth: "400px" }}
      >
        <h3 className="text-center mb-3">
          {mode === "signup" ? "Register" : "Sign In"}
        </h3>

        {/* Switch between Email/Phone */}
        <div className="btn-group w-100 mb-3">
          <button
            type="button"
            className={`btn btn-sm ${
              method === "email" ? "btn-primary" : "btn-outline-primary"
            }`}
            onClick={() => setMethod("email")}
          >
            Email
          </button>
          <button
            type="button"
            className={`btn btn-sm ${
              method === "phone" ? "btn-primary" : "btn-outline-primary"
            }`}
            onClick={() => setMethod("phone")}
          >
            Phone (OTP)
          </button>
        </div>

        {/* Email form */}
        {method === "email" && (
          <form onSubmit={handleEmailAuth}>
            <div className="mb-3">
              <label>Email</label>
              <input
                type="email"
                className="form-control"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
            <div className="mb-3">
              <label>Password</label>
              <input
                type="password"
                className="form-control"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
            {mode === "signup" && (
              <div className="mb-3">
                <label>Confirm Password</label>
                <input
                  type="password"
                  className="form-control"
                  value={rePassword}
                  onChange={(e) => setRePassword(e.target.value)}
                  required
                />
              </div>
            )}
            <button type="submit" className="btn btn-success w-100">
              {mode === "signup" ? "Register" : "Sign In"}
            </button>
          </form>
        )}

        {/* Phone OTP form */}
        {method === "phone" && (
          <div>
            <div className="mb-3">
              <label>Phone (with country code)</label>
              <input
                type="text"
                className="form-control"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="+919876543210"
                required
              />
            </div>
            <button className="btn btn-primary w-100 mb-2" onClick={sendOtp}>
              Send OTP
            </button>
            <div className="mb-3">
              <label>Enter OTP</label>
              <input
                type="text"
                className="form-control"
                value={otp}
                onChange={(e) => setOtp(e.target.value)}
              />
            </div>
            <button className="btn btn-success w-100" onClick={verifyOtp}>
              Verify OTP
            </button>
          </div>
        )}

        {/* Google login */}
        <div className="text-center mt-3">
          <button
            type="button"
            className="btn btn-danger w-100"
            onClick={handleGoogleLogin}
          >
            Sign in with Google
          </button>
        </div>

        {/* Toggle register/signin */}
        <div className="text-center mt-3">
          {mode === "signup" ? (
            <p>
              Already have an account?{" "}
              <button
                type="button"
                className="btn btn-link p-0"
                onClick={() => setMode("signin")}
              >
                Sign In
              </button>
            </p>
          ) : (
            <p>
              New here?{" "}
              <button
                type="button"
                className="btn btn-link p-0"
                onClick={() => setMode("signup")}
              >
                Register
              </button>
            </p>
          )}
        </div>
      </div>

      {/* Recaptcha container */}
      <div id="recaptcha-container"></div>
    </div>
  );
}
