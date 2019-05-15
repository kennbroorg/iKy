import { Component, OnInit, OnDestroy, Input, ViewChild, ElementRef, AfterViewInit } from '@angular/core';
import { NbThemeService } from '@nebular/theme';

@Component({
    selector: 'ngx-twitter-resume',
    templateUrl: './twitter-resume.component.html',
    styleUrls: ['./twitter-resume.component.scss']
})
export class TwitterResumeComponent implements OnInit, AfterViewInit {
    colorScheme: any;
    themeSubscription: any;

    @ViewChild('nbCardTwitterResume') private cardContainer: ElementRef;
    @Input() private data: any;
    private twitterResume : any;
    private validation : any;

    private card: any;
    private width: number;
    private height: number;

    constructor(private theme: NbThemeService) {
        this.themeSubscription = this.theme.getJsTheme().subscribe(config => {
            const colors: any = config.variables;
            this.colorScheme = {
                domain: [colors.primaryLight, colors.infoLight, colors.successLight, colors.warningLight, colors.dangerLight],
            };
        });
    }

    ngOnInit() {

        //this.card = this.cardContainer.nativeElement;
        //this.width = this.card.clientWidth;
        //this.height = this.width * 0.68;

        //console.log("Twitter Resume Component");

        //this.twitterResume = this.data.result[4].graphic[0].resume.children.map(this.arrayAdecuate);
        //console.log("Twitter Resume data", this.twitterResume);
        //this.validation = this.data.result[2].validation;

        ///* Validation */
        //switch(this.data.result[2].validation) {
        //    case 'hard':
        //        this.validation = 'success';
        //        break;
        //    case 'soft':
        //        this.validation = 'warning';
        //        break;
        //    case 'no':
        //        this.validation = 'danger';
        //        break;
        //    default:
        //        this.validation = 'danger';
        //}
    }

    ngAfterViewInit() {
        this.card = this.cardContainer.nativeElement;
        this.width = this.cardContainer.nativeElement.parentNode.parentNode.clientWidth;
        this.height = this.cardContainer.nativeElement.parentNode.parentNode.clientHeight - 55;
        console.log("CARD-------------------------------", this.card);
        console.log("WIDTH-------------------------------", this.width);
        console.log("HEIGHT-------------------------------", this.height);
        console.log("Twitter Resume Component");

        this.twitterResume = this.data.result[4].graphic[0].resume.children.map(this.arrayAdecuate);
        console.log("Twitter Resume data", this.twitterResume);
        this.validation = this.data.result[2].validation;

        /* Validation */
        switch(this.data.result[2].validation) {
            case 'hard':
                this.validation = 'success';
                break;
            case 'soft':
                this.validation = 'warning';
                break;
            case 'no':
                this.validation = 'danger';
                break;
            default:
                this.validation = 'danger';
        }
    }

    ngOnDestroy(): void {
        this.themeSubscription.unsubscribe();
    }

    arrayAdecuate(item, index, array) {
        if (array[index]['total']) {
            array[index].value = array[index]['total'];
            delete array[index].total;  
        }
        return item;
    }

}
