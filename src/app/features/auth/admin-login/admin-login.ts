import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { RouterModule } from '@angular/router';
import { ApiService } from '../../../core/services/api';

@Component({
  selector: 'app-admin-login',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterModule],
  templateUrl: './admin-login.html',
  styleUrls: ['./admin-login.css']
})
export class AdminLoginComponent implements OnInit {

  loginForm!: FormGroup;
  messages: string[] = [];

  // State variable to manage password visibility
  isPasswordVisible = false;

  constructor(
    private fb: FormBuilder,
    private router: Router,
    private api: ApiService
  ) { }

  ngOnInit(): void {
    // Initialize the reactive form
    this.loginForm = this.fb.group({
      username: ['', Validators.required],
      password: ['', Validators.required]
    });
  }

  // Flips the boolean state, which updates the HTML automatically
  togglePassword(): void {
    this.isPasswordVisible = !this.isPasswordVisible;
  }

  onSubmit(): void {
    if (!this.loginForm.valid) {
      this.messages = ['Please enter both username and password.'];
      return;
    }

    const { username, password } = this.loginForm.value;
    console.log('Login attempt with:', username);

    this.api.adminLogin({ username, password }).subscribe({
      next: () => {
        this.messages = [];
        this.router.navigate(['/admin-otp']);
      },
      error: (err: any) => {
        if (err?.status === 403 && err?.error?.requires_otp) {
          this.router.navigate(['/admin-otp']);
          return;
        }
        this.messages = [err?.error?.error || 'Login failed. Please try again.'];
      }
    });
  }

}