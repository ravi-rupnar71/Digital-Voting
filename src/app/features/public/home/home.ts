import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';

@Component({
  selector: 'app-voting-home',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './home.html',
  styleUrls: ['./home.css'] // Ensure this points to your style.css logic
})
export class VotingHomeComponent implements OnInit {
  
  // This array replaces the Flask flashed messages. 
  // In a real app, you might populate this from a NotificationService or State.
  messages: string[] = [];

  constructor() { }

  ngOnInit(): void {
    // Example: Mocking a flash message on load
    // this.messages = ['Welcome to the Digital Voting System'];
  }

}