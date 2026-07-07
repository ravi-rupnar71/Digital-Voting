import { ComponentFixture, TestBed } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';

import { VoterLoginComponent } from './voter-login';

describe('VoterLoginComponent', () => {
  let component: VoterLoginComponent;
  let fixture: ComponentFixture<VoterLoginComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [VoterLoginComponent, RouterTestingModule],
    }).compileComponents();

    fixture = TestBed.createComponent(VoterLoginComponent);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
