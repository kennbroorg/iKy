import { Component, OnInit, Input } from '@angular/core';
import { Pipe, Sanitizer } from '@angular/core';
import { NbPopoverDirective, NbPosition, NbTrigger } from '@nebular/theme';

@Component({
    selector: 'ngx-github-calendar',
    templateUrl: './github-calendar.component.html',
    styleUrls: ['./github-calendar.component.scss']
})
export class GithubCalendarComponent implements OnInit {
    @Input() private data: any;
    private githubCalendar : any;
    private githubCalendarPrev : any;
    private validation : any;

    constructor() {}

    ngOnInit() {
        console.log("Init github calendar");

        this.githubCalendar = this.data.result[4].graphic[1].cal_actual;
        this.githubCalendarPrev = this.data.result[4].graphic[2].cal_previous;
    }
}
