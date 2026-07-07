import { ComponentFixture, TestBed } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';

import { VotingHomeComponent } from './home';

describe('VotingHomeComponent', () => {
  let component: VotingHomeComponent;
  let fixture: ComponentFixture<VotingHomeComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [VotingHomeComponent, RouterTestingModule],
    }).compileComponents();

    fixture = TestBed.createComponent(VotingHomeComponent);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
