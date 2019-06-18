import { ChangeDetectionStrategy, Component, OnInit, OnDestroy, ViewChild, ElementRef } from '@angular/core';
import { NbThemeService } from '@nebular/theme';
import { DomSanitizer, SafeUrl } from '@angular/platform-browser';

// Search
import { NbSearchService } from '@nebular/theme';

// RxJS
import { takeWhile } from 'rxjs/operators' ;
import { Observable } from 'rxjs/Observable';
import { mergeMap } from 'rxjs/operators';

// Toaster 
import { ToasterConfig } from 'angular2-toaster';
import 'style-loader!angular2-toaster/toaster.css';
import { NbGlobalLogicalPosition, NbGlobalPhysicalPosition, NbGlobalPosition, NbToastrService } from '@nebular/theme';
import { NbToastStatus } from '@nebular/theme/components/toastr/model';


// Data Service
import { DataGatherInfoService } from '../../@core/data/data-gather-info.service';

// Report
import * as jsPDF from 'jspdf';
import 'jspdf-autotable';
declare let canvg: any;
declare let svgAsPngUri: any;
declare let saveSvgAsPng: any;
import * as html2canvas from "html2canvas";

@Component({
    selector: 'ngx-gatherer',
    styleUrls: ['./gatherer.component.scss'],
    templateUrl: './gatherer.component.html',
    changeDetection: ChangeDetectionStrategy.Default
})

export class GathererComponent implements OnInit {
    @ViewChild('pageGather') private nbCardContainer: ElementRef;
    public  gathered: any = [];
    public  processing: boolean = false;
    public  searchSubs: any;
    public  svg: any;
    public  img: any;
    public  divInvisible: any;
    public  getCanvas: any;
    public  downloadJsonHref: any;
    public  timeline: any = [];
    public  profile: any = [];
    public  name: any = [];
    public  location: any = [];
    public  gender: any = [];
    public  social: any = [];
    public  photo: any = [];
    public  organization: any = [];

    public  validationShow = {
        hard: true,
        soft: true,
        no: true,
    };


    constructor(private searchService: NbSearchService, 
                private sanitizer: DomSanitizer,
                private dataGatherService: DataGatherInfoService) {
    }

    ngOnInit() {
        this.searchSubs = this.searchService.onSearchSubmit()
          .subscribe((data: any) => {
            // Initialize global data
            this.gathered = this.dataGatherService.initialize();
            console.log("Global data initialize", this.gathered);

            console.log("Search", data);
            this.gathered = this.dataGatherService.validateEmail(data.term); 
        })

        console.log("GathererComponent ngOnInit")
        // Check global data
        this.gathered = this.dataGatherService.pullGather();
        console.log("GathererComponent ngOnInit", this.gathered)
        console.log("GathererComponent ngOnInit length", this.jsonLength(this.gathered))
    }

    ngOnDestroy () {
        this.searchSubs.unsubscribe();
    }

    generateDownloadJsonUri() {
        let sJson = JSON.stringify(this.gathered);
        let element = document.createElement('a');
        element.setAttribute('href', "data:text/json;charset=UTF-8," + encodeURIComponent(sJson));
        element.setAttribute('download', "gathered.json");
        element.style.display = 'none';
        document.body.appendChild(element);
        element.click(); // simulate click
        document.body.removeChild(element);
    }

    jsonLength(obj: any) {
        try {
          return Object.keys(obj).length;
        }
        catch(e) {
          return 0;
        }
    }

    setValidation(val: any) {
        this.validationShow[val] = !this.validationShow[val];
        console.log(this.validationShow);
    }

    checkValidation(val: any) {
        return this.validationShow[val]
    }

    // As All Functions in js are asynchronus, to use await i am using async here
    async generateAllPdf() {
        this.processing = true;
        var infoText: string;
        let moduleHeight: number;
        this.profile = [];
        this.timeline = [];
        this.name = [];
        this.location = [];
        this.gender = [];
        this.organization = [];
        this.social = [];
        this.photo = [];

        const doc = new jsPDF('p', 'mm', 'a4');
        var pageHeight = doc.internal.pageSize.height;

        doc.setFontSize(17);
        doc.setFontStyle("bold");
        doc.text('iKy Report', 105, 80, null, null, 'center');
        doc.addPage();
        var hl = 20;

        doc.setDrawColor(32, 61, 79);
        doc.setFillColor(32, 61, 79);
        doc.rect(10, hl, 190, 7, 'F');
        doc.rect(10, hl, 190, 13); 
        
        doc.setFontSize(11);
        doc.setTextColor(255, 255, 255);
        doc.text('Analyzed email', 105, hl + 5, null, null, 'center');
        doc.setFontSize(11);
        doc.setTextColor(0, 0, 0);
        doc.text(this.gathered['email'], 105, hl + 11, null, null, 'center');
        hl = hl + 20;

        doc.setFontSize(11);
        doc.setDrawColor(32, 61, 79);
        doc.setFillColor(32, 61, 79);
        doc.rect(10, hl, 190, 7, 'F');
        doc.setTextColor(255, 255, 255);
        doc.text('Information gathered', 105, hl + 5, null, null, 'center');
        hl = hl + 11;

        // Fullcontact module report
        if (this.gathered['fullcontact'] && this.gathered['fullcontact']['result'] && 
              this.gathered['fullcontact']['result'].length > 3) {
            moduleHeight = 80;

            // Validate pageHeight
            if ( hl + moduleHeight > pageHeight) {
                doc.addPage();
                hl = 20;
            }

            doc.setFontSize(11);
            doc.setDrawColor(44, 93, 126);
            doc.setFillColor(44, 93, 126);
            doc.rect(10, hl, 190, 7, 'F');
            doc.setTextColor(255, 255, 255);
            doc.text('Module fullcontact', 105, hl + 5, null, null, 'center');
            hl = hl + 10;

            var svg = this.nbCardContainer.nativeElement.querySelector("#divFullcontactGraphs");
            await html2canvas(svg.children[0], { 
                scale: 1,
                useCORS: true, 
                // foreignObjectRendering: true,  // Render with the background but only if the div is in the screen
                async: true,
                logging: true,
                backgroundColor: "#51A5D7",
                allowTaint: true,
                removeContainer: true
                })
                .then(function (canvas) { 
                    doc.addImage(canvas.toDataURL('image/png'), 'JPEG', 10, hl, 75, 65);
                });

            doc.setFontSize(11);
            doc.setFont('helvetica', 'normal');
            doc.setTextColor(79, 79, 79);
            infoText = 'The information collected by the fullcontact module represented in the graph on the left shows the RRSS related to the e-mail analyzed.\n\nThe graph shows nodes, which have the name of the RRSS as upper title and the username in the lower part.\n\nThe information shown in the graph is shown in the table below.'
            var splitText = doc.splitTextToSize(infoText, 110);
            var y = 6;
            for (var i=0; i<splitText.length; i++){
                doc.text(90, hl + y, splitText[i]);
                y = y + 4;
            }
            hl = hl + 70;

            // Information table  TODO: Repair
            if (this.gathered['fullcontact']['result'][5]['profile'][5]['social']) {
                let headTable = [];
                let bodyTable = [];
                let elem = [];
                let i: any;
                let list = this.gathered['fullcontact']['result'][5]['profile'][5]['social'];
                
                for (let i in list) {
                    elem = [list[i]['name'], list[i]['username'], list[i]['url']];
                    bodyTable.push(elem);
                }
        
                doc.autoTable({
                    startY: hl,
                    head: [
                        ['RRSS', 'Username', 'Link'],
                    ],
                    body: bodyTable,
                });
            
                let finalY = doc.previousAutoTable.finalY;
                doc.autoTable({
                    startY: finalY,
                    // html: '.table',
                    useCss: true,
                });
        
                hl = finalY
            }
        }

        hl = hl + 10; // Space between modules


        // Twitter module report
        if (this.gathered['twitter'] && this.gathered['twitter']['result'] &&
              this.gathered['twitter']['result'].length > 3) {

            // Mentions user
            moduleHeight = 80;

            // Validate pageHeight
            if ( hl + moduleHeight > pageHeight) {
                doc.addPage();
                hl = 20;
            }

            doc.setFontSize(11);
            doc.setDrawColor(44, 93, 126);
            doc.setFillColor(44, 93, 126);
            doc.rect(10, hl, 190, 7, 'F');
            doc.setTextColor(255, 255, 255);
            doc.text('Module twitter', 105, hl + 5, null, null, 'center');
            hl = hl + 10;

            var svg = this.nbCardContainer.nativeElement.querySelector("#divTwitterList");
            await html2canvas(svg.children[0], { 
                scale: 1,
                useCORS: true, 
                // foreignObjectRendering: true,  // Render with the background but only if the div is in the screen
                async: true,
                logging: true,
                backgroundColor: "#51A5D7",
                allowTaint: true,
                removeContainer: true
                })
                .then(function (canvas) { 
                    doc.addImage(canvas.toDataURL('image/png'), 'JPEG', 10, hl, 75, 65);
                });

            // Information table
            if (this.gathered['twitter']['result'][4]['graphic'][5]['tweetslist']) {
                let headTable = [];
                let bodyTable = [];
                let elem = [];
                let i: any;
                let list = this.gathered['twitter']['result'][4]['graphic'][5]['tweetslist'];
                
                for (let i in list) {
                    for (let y in  list[i]['series']) {
                        elem = [list[i]['name'], list[i]['series'][y]['name'], list[i]['series'][y]['value']];
                        bodyTable.push(elem);
                    }
                }

                doc.autoTable({
                    startY: hl + 5,
                    margin: {left: 90},
                    showHead: false,
                    bodyStyles: {
                        fillColor: [52, 73, 94],
                        textColor: 240
                    },
                    alternateRowStyles: {
                        fillColor: [74, 96, 117]
                    },
                    head: [
                        ['Period', 'Type', 'Value'],
                    ],
                    body: bodyTable,
                });
            }

            hl = hl + 70;

            // Resume
            moduleHeight = 70;

            // Validate pageHeight
            if ( hl + moduleHeight > pageHeight) {
                doc.addPage();
                hl = 20;
            }

            var svg = this.nbCardContainer.nativeElement.querySelector("#divTwitterResume");
            await html2canvas(svg.children[0], { 
                scale: 1,
                useCORS: true, 
                // foreignObjectRendering: true,  // Render with the background but only if the div is in the screen
                async: true,
                logging: true,
                backgroundColor: "#51A5D7",
                allowTaint: true,
                removeContainer: true
                })
                .then(function (canvas) { 
                    doc.addImage(canvas.toDataURL('image/png'), 'JPEG', 10, hl, 75, 65);
                });

            // Information table
            if (this.gathered['twitter']['result'][4]['graphic'][0]['resume']['children']) {
                let headTable = [];
                let bodyTable = [];
                let elem = [];
                let i: any;
                let list = this.gathered['twitter']['result'][4]['graphic'][0]['resume']['children'];
                
                for (let i in list) {
                    elem = [list[i]['name'], list[i]['value']];
                    bodyTable.push(elem);
                }

                doc.autoTable({
                    startY: hl + 5,
                    margin: {left: 90},
                    showHead: false,
                    bodyStyles: {
                        fillColor: [52, 73, 94],
                        textColor: 240
                    },
                    alternateRowStyles: {
                        fillColor: [74, 96, 117]
                    },
                    head: [
                        ['Name', 'Value'],
                    ],
                    body: bodyTable,
                });
            }

            hl = hl + 70;

            // Popularity
            moduleHeight = 70;

            // Validate pageHeight
            if ( hl + moduleHeight > pageHeight) {
                doc.addPage();
                hl = 20;
            }

            var svg = this.nbCardContainer.nativeElement.querySelector("#divTwitterPopularity");
            await html2canvas(svg.children[0], { 
                scale: 1,
                useCORS: true, 
                // foreignObjectRendering: true,  // Render with the background but only if the div is in the screen
                async: true,
                logging: true,
                backgroundColor: "#51A5D7",
                allowTaint: true,
                removeContainer: true
                })
                .then(function (canvas) { 
                    doc.addImage(canvas.toDataURL('image/png'), 'JPEG', 10, hl, 75, 65);
                });

            // Information table
            if (this.gathered['twitter']['result'][4]['graphic'][1]['popularity']) {
                let headTable = [];
                let bodyTable = [];
                let elem = [];
                let i: any;
                let list = this.gathered['twitter']['result'][4]['graphic'][1]['popularity'];
                
                for (let i in list) {
                    elem = [list[i]['name'], list[i]['value']];
                    bodyTable.push(elem);
                }

                doc.autoTable({
                    startY: hl + 5,
                    margin: {left: 90},
                    showHead: false,
                    bodyStyles: {
                        fillColor: [52, 73, 94],
                        textColor: 240
                    },
                    alternateRowStyles: {
                        fillColor: [74, 96, 117]
                    },
                    head: [
                        ['Name', 'Value'],
                    ],
                    body: bodyTable,
                });
            }

            hl = hl + 70;

            // Approval
            moduleHeight = 70;

            // Validate pageHeight
            if ( hl + moduleHeight > pageHeight) {
                doc.addPage();
                hl = 20;
            }

            var svg = this.nbCardContainer.nativeElement.querySelector("#divTwitterApproval");
            await html2canvas(svg.children[0], { 
                scale: 1,
                useCORS: true, 
                // foreignObjectRendering: true,  // Render with the background but only if the div is in the screen
                async: true,
                logging: true,
                backgroundColor: "#51A5D7",
                allowTaint: true,
                removeContainer: true
                })
                .then(function (canvas) { 
                    doc.addImage(canvas.toDataURL('image/png'), 'JPEG', 10, hl, 75, 65);
                });

            // Information table
            if (this.gathered['twitter']['result'][4]['graphic'][2]['approval']) {
                let headTable = [];
                let bodyTable = [];
                let elem = [];
                let i: any;
                let list = this.gathered['twitter']['result'][4]['graphic'][2]['approval'];
                
                for (let i in list) {
                    elem = [list[i]['name'], list[i]['value']];
                    bodyTable.push(elem);
                }

                doc.autoTable({
                    startY: hl + 5,
                    margin: {left: 90},
                    showHead: false,
                    bodyStyles: {
                        fillColor: [52, 73, 94],
                        textColor: 240
                    },
                    alternateRowStyles: {
                        fillColor: [74, 96, 117]
                    },
                    head: [
                        ['Name', 'Value'],
                    ],
                    body: bodyTable,
                });
            }

            hl = hl + 70;

            // Hashtag
            moduleHeight = 70;

            // Validate pageHeight
            if ( hl + moduleHeight > pageHeight) {
                doc.addPage();
                hl = 20;
            }

            var svg = this.nbCardContainer.nativeElement.querySelector("#divTwitterHashtag");
            await html2canvas(svg.children[0], { 
                scale: 1,
                useCORS: true, 
                // foreignObjectRendering: true,  // Render with the background but only if the div is in the screen
                async: true,
                logging: true,
                backgroundColor: "#51A5D7",
                allowTaint: true,
                removeContainer: true
                })
                .then(function (canvas) { 
                    doc.addImage(canvas.toDataURL('image/png'), 'JPEG', 10, hl, 75, 65);
                });

            // Information table
            if (this.gathered['twitter']['result'][4]['graphic'][3]['hashtag']) {
                let headTable = [];
                let bodyTable = [];
                let elem = "";
                let i: any;
                let list = this.gathered['twitter']['result'][4]['graphic'][3]['hashtag'];
                
                for (let i in list) {
                    elem = elem + list[i]['label'] + " ";
                }
                bodyTable.push([elem]);

                doc.autoTable({
                    startY: hl + 5,
                    margin: {left: 90},
                    showHead: true,
                    styles: { overflow: 'linebreak', cellWidth: 'wrap', halign: 'center' },
                    columnStyles: { 0: { cellWidth: 'auto' } },
                    bodyStyles: {
                        fillColor: [52, 73, 94],
                        textColor: 240
                    },
                    alternateRowStyles: {
                        fillColor: [74, 96, 117]
                    },
                    head: [
                        ['Hashtags'],
                    ],
                    body: bodyTable,
                });
            }

            hl = hl + 70;

            // Mentions
            moduleHeight = 70;

            // Validate pageHeight
            if ( hl + moduleHeight > pageHeight) {
                doc.addPage();
                hl = 20;
            }

            var svg = this.nbCardContainer.nativeElement.querySelector("#divTwitterUsers");
            await html2canvas(svg.children[0], { 
                scale: 1,
                useCORS: true, 
                // foreignObjectRendering: true,  // Render with the background but only if the div is in the screen
                async: true,
                logging: true,
                backgroundColor: "#51A5D7",
                allowTaint: true,
                removeContainer: true
                })
                .then(function (canvas) { 
                    doc.addImage(canvas.toDataURL('image/png'), 'JPEG', 10, hl, 75, 65);
                });

            // Information table
            if (this.gathered['twitter']['result'][4]['graphic'][4]['users']) {
                let headTable = [];
                let bodyTable = [];
                let elem = "";
                let i: any;
                let list = this.gathered['twitter']['result'][4]['graphic'][4]['users'];
                
                for (let i in list) {
                    elem = elem + list[i]['title'] + ' ';
                }
                bodyTable.push([elem]);

                doc.autoTable({
                    startY: hl,
                    margin: {left: 90},
                    showHead: true,
                    styles: { overflow: 'linebreak', cellWidth: 'wrap', halign: 'center' },
                    columnStyles: { 0: { cellWidth: 'auto' } },
                    bodyStyles: {
                        fillColor: [52, 73, 94],
                        textColor: 240
                    },
                    alternateRowStyles: {
                        fillColor: [74, 96, 117]
                    },
                    head: [
                        ['Mentions to users'],
                    ],
                    body: bodyTable,
                });
            }

            if (doc.previousAutoTable.finalY > hl + 70) {
                hl = doc.previousAutoTable.finalY
            }
            else {
                hl = hl + 70;
            }
        }

        hl = hl + 5; // Space between modules


        // Github module report
        if (this.gathered['github'] && this.gathered['github']['result'] &&
                this.gathered['github']['result'].length > 3) {

            // Resume
            moduleHeight = 80;

            // Validate pageHeight
            if ( hl + moduleHeight > pageHeight) {
                doc.addPage();
                hl = 20;
            }

            doc.setFontSize(11);
            doc.setDrawColor(44, 93, 126);
            doc.setFillColor(44, 93, 126);
            doc.rect(10, hl, 190, 7, 'F');
            doc.setTextColor(255, 255, 255);
            doc.text('Module github', 105, hl + 5, null, null, 'center');
            hl = hl + 10;

            var svg = this.nbCardContainer.nativeElement.querySelector("#divGithubGraphs");
            await html2canvas(svg.children[0], { 
                scale: 1,
                useCORS: true, 
                // foreignObjectRendering: true,  // Render with the background but only if the div is in the screen
                async: true,
                logging: true,
                backgroundColor: "#51A5D7",
                allowTaint: true,
                removeContainer: true
                })
                .then(function (canvas) { 
                    doc.addImage(canvas.toDataURL('image/png'), 'JPEG', 10, hl, 75, 65);
                });

            doc.setFontSize(11);
            doc.setFont('helvetica', 'normal');
            doc.setTextColor(79, 79, 79);
            infoText = 'The information of the chart is shown in the following table.';
            var splitText = doc.splitTextToSize(infoText, 110);
            var y = 6;
            for (var i=0; i<splitText.length; i++){
                doc.text(90, hl + y, splitText[i]);
                y = y + 4;
            }

            // Information table
            if (this.gathered['github']['result'][4]['graphic'][0]['github']) {
                let headTable = [];
                let bodyTable = [];
                let elem = [];
                let i: any;
                let list = this.gathered['github']['result'][4]['graphic'][0]['github'];
                
                for (let i in list) {
                    if (list[i]['title'] != 'Github' && list[i]['subtitle']) {
                        elem = [list[i]['title'], list[i]['subtitle']];
                        bodyTable.push(elem);
                    }
                }

                doc.autoTable({
                    startY: hl + 11,
                    margin: {left: 90},
                    showHead: false,
                    bodyStyles: {
                        fillColor: [52, 73, 94],
                        textColor: 240
                    },
                    alternateRowStyles: {
                        fillColor: [74, 96, 117]
                    },
                    head: [
                        ['Name', 'Value'],
                    ],
                    body: bodyTable,
                });
            }

            hl = hl + 70;

            // Github Calendar
            moduleHeight = 70;

            // Validate pageHeight
            if ( hl + moduleHeight > pageHeight) {
                doc.addPage();
                hl = 20;
            }

            var svg = this.nbCardContainer.nativeElement.querySelector("#divGithubCalendar");
            await html2canvas(svg.children[0], { 
                scale: 1,
                useCORS: true, 
                // foreignObjectRendering: true,  // Render with the background but only if the div is in the screen
                async: true,
                logging: true,
                backgroundColor: "#51A5D7",
                allowTaint: true,
                removeContainer: true
                })
                .then(function (canvas) { 
                    doc.addImage(canvas.toDataURL('image/png'), 'JPEG', 30, hl, 150, 65);
                });

            hl = hl + 70;

        }

        hl = hl + 5; // Space between modules

        // Linkedin module report   TODO Agregar la condicion de existencia y longitud
        if (this.gathered['linkedin'] && this.gathered['linkedin']['result'] && 
                this.gathered['linkedin']['result'].length > 3) {
            moduleHeight = 80;

            // Validate pageHeight
            if ( hl + moduleHeight > pageHeight) {
                doc.addPage();
                hl = 20;
            }

            // Linkedin Social
            doc.setFontSize(11);
            doc.setDrawColor(44, 93, 126);
            doc.setFillColor(44, 93, 126);
            doc.rect(10, hl, 190, 7, 'F');
            doc.setTextColor(255, 255, 255);
            doc.text('Module linkedin', 105, hl + 5, null, null, 'center');
            hl = hl + 10;

            var svg = this.nbCardContainer.nativeElement.querySelector("#divLinkedinGraphs");
            await html2canvas(svg.children[0], { 
                scale: 1,
                useCORS: true, 
                // foreignObjectRendering: true,  // Render with the background but only if the div is in the screen
                async: true,
                logging: true,
                backgroundColor: "#51A5D7",
                allowTaint: true,
                removeContainer: true
                })
                .then(function (canvas) { 
                    doc.addImage(canvas.toDataURL('image/png'), 'JPEG', 10, hl, 75, 65);
                });

            doc.setFontSize(11);
            doc.setFont('helvetica', 'normal');
            doc.setTextColor(79, 79, 79);
            infoText = 'The information of the chart is shown in the following table.';
            var splitText = doc.splitTextToSize(infoText, 110);
            var y = 6;
            for (var i=0; i<splitText.length; i++){
                doc.text(90, hl + y, splitText[i]);
                y = y + 4;
            }

            // Information table
            if (this.gathered['linkedin']['result'][4]['graphic'][0]['social']) {
                let headTable = [];
                let bodyTable = [];
                let elem = [];
                let i: any;
                let list = this.gathered['linkedin']['result'][4]['graphic'][0]['social'];
                
                for (let i in list) {
                    if (list[i]['title'] != 'Linkedin' && list[i]['subtitle']) {
                        elem = [list[i]['title'], list[i]['subtitle']];
                        bodyTable.push(elem);
                    }
                }

                doc.autoTable({
                    startY: hl + 11,
                    margin: {left: 90},
                    showHead: false,
                    styles: { overflow: 'hidden' },
                    bodyStyles: {
                        fillColor: [52, 73, 94],
                        textColor: 240
                    },
                    alternateRowStyles: {
                        fillColor: [74, 96, 117]
                    },
                    head: [
                        ['Name', 'Value'],
                    ],
                    body: bodyTable,
                });
            }

            hl = hl + 70;

            // Linkedin Skill
            moduleHeight = 80;

            // Validate pageHeight
            if ( hl + moduleHeight > pageHeight) {
                doc.addPage();
                hl = 20;
            }

            var svg = this.nbCardContainer.nativeElement.querySelector("#divLinkedinBubble");
            await html2canvas(svg.children[0], { 
                scale: 1,
                useCORS: true, 
                // foreignObjectRendering: true,  // Render with the background but only if the div is in the screen
                async: true,
                logging: true,
                backgroundColor: "#51A5D7",
                allowTaint: true,
                removeContainer: true
                })
                .then(function (canvas) { 
                    doc.addImage(canvas.toDataURL('image/png'), 'JPEG', 10, hl, 75, 65);
                });

            doc.setFontSize(11);
            doc.setFont('helvetica', 'normal');
            doc.setTextColor(79, 79, 79);
            infoText = 'Principal skill.';
            var splitText = doc.splitTextToSize(infoText, 110);
            var y = 6;
            for (var i=0; i<splitText.length; i++){
                doc.text(90, hl + y, splitText[i]);
                y = y + 4;
            }

            // Information table
            if (this.gathered['linkedin']['result'][4]['graphic'][1]['skills']['children']) {
                let headTable = [];
                let bodyTable = [];
                let elem = [];
                let i: any;
                let list = this.gathered['linkedin']['result'][4]['graphic'][1]['skills']['children'];
                
                for (let i in list) {
                    if (Number(i) < 6) {
                        elem = [list[i]['name'], list[i]['value']];
                        bodyTable.push(elem);
                    }
                }

                doc.autoTable({
                    startY: hl + 11,
                    margin: {left: 90},
                    showHead: false,
                    styles: { overflow: 'hidden' },
                    bodyStyles: {
                        fillColor: [52, 73, 94],
                        textColor: 240
                    },
                    alternateRowStyles: {
                        fillColor: [74, 96, 117]
                    },
                    head: [
                        ['Skill', 'Value'],
                    ],
                    body: bodyTable,
                });
            }

            hl = hl + 70;

            // Information table Certifications
            if (this.gathered['linkedin']['result'][4]['graphic'][2]['certificationView']) {
                let headTable = [];
                let bodyTable = [];
                let elem = [];
                let i: any;
                let list = this.gathered['linkedin']['result'][4]['graphic'][2]['certificationView'];
                
                for (let i in list) {
                    elem = [list[i]['name'], list[i]['desc']];
                    bodyTable.push(elem);
                }
        
                headTable = [['title']]
                headTable[0][0] = {content: 'Certifications', colSpan: 2, styles: {halign: 'center', fillColor: [22, 160, 133]}};
                doc.autoTable({
                    startY: hl,
                    head: headTable, 
                    body: bodyTable,
                });
            
                let finalY = doc.previousAutoTable.finalY;
        
                hl = finalY
            }
            // Information table Positions
            if (this.gathered['linkedin']['result'][4]['graphic'][3]['positionGroupView']) {
                let headTable = [];
                let bodyTable = [];
                let elem = [];
                let i: any;
                let list = this.gathered['linkedin']['result'][4]['graphic'][3]['positionGroupView'];
                
                for (let i in list) {
                    elem = [list[i]['label']];
                    bodyTable.push(elem);
                }
        
                headTable = [['title']]
                headTable[0][0] = {content: 'Positions', colSpan: 1, styles: {halign: 'center', fillColor: [22, 160, 133]}};
                doc.autoTable({
                    startY: hl + 4,
                    head: headTable, 
                    body: bodyTable,
                    margin: 40,
                });
            
                let finalY = doc.previousAutoTable.finalY;
        
                hl = finalY
            }
        }

        hl = hl + 10; // Space between modules

        // Keybase module report
        if (this.gathered['keybase'] && this.gathered['keybase']['result'] &&
               this.gathered['keybase']['result'].length > 3) {
            moduleHeight = 80;

            // Validate pageHeight
            if ( hl + moduleHeight > pageHeight) {
                doc.addPage();
                hl = 20;
            }

            // Keybase Social
            doc.setFontSize(11);
            doc.setDrawColor(44, 93, 126);
            doc.setFillColor(44, 93, 126);
            doc.rect(10, hl, 190, 7, 'F');
            doc.setTextColor(255, 255, 255);
            doc.text('Module keybase', 105, hl + 5, null, null, 'center');
            hl = hl + 10;

            var svg = this.nbCardContainer.nativeElement.querySelector("#divKeybaseSocial");
            await html2canvas(svg.children[0], { 
                scale: 1,
                useCORS: true, 
                // foreignObjectRendering: true,  // Render with the background but only if the div is in the screen
                async: true,
                logging: true,
                backgroundColor: "#51A5D7",
                allowTaint: true,
                removeContainer: true
                })
                .then(function (canvas) { 
                    doc.addImage(canvas.toDataURL('image/png'), 'JPEG', 10, hl, 75, 65);
                });

            doc.setFontSize(11);
            doc.setFont('helvetica', 'normal');
            doc.setTextColor(79, 79, 79);
            infoText = 'The information of the chart is shown in the following table.';
            var splitText = doc.splitTextToSize(infoText, 110);
            var y = 6;
            for (var i=0; i<splitText.length; i++){
                doc.text(90, hl + y, splitText[i]);
                y = y + 4;
            }

            // Information table
            if (this.gathered['keybase']['result'][4]['graphic'][0]['keysocial']) {
                let headTable = [];
                let bodyTable = [];
                let elem = [];
                let i: any;
                let list = this.gathered['keybase']['result'][4]['graphic'][0]['keysocial'];
                
                for (let i in list) {
                    if (list[i]['title'] != 'KeybaseSocial' && list[i]['subtitle']) {
                        if (Number(i) < 8) {
                            elem = [list[i]['title'], list[i]['subtitle']];
                            bodyTable.push(elem);
                        }
                    }
                }

                doc.autoTable({
                    startY: hl + 11,
                    margin: {left: 90},
                    showHead: false,
                    styles: { overflow: 'hidden' },
                    bodyStyles: {
                        fillColor: [52, 73, 94],
                        textColor: 240
                    },
                    alternateRowStyles: {
                        fillColor: [74, 96, 117]
                    },
                    head: [
                        ['Name', 'Value'],
                    ],
                    body: bodyTable,
                });
            }

            hl = hl + 70;

            // Keybase Device
            moduleHeight = 80;

            // Validate pageHeight
            if ( hl + moduleHeight > pageHeight) {
                doc.addPage();
                hl = 20;
            }

            var svg = this.nbCardContainer.nativeElement.querySelector("#divKeybaseDevices");
            await html2canvas(svg.children[0], { 
                scale: 1,
                useCORS: true, 
                // foreignObjectRendering: true,  // Render with the background but only if the div is in the screen
                async: true,
                logging: true,
                backgroundColor: "#51A5D7",
                allowTaint: true,
                removeContainer: true
                })
                .then(function (canvas) { 
                    doc.addImage(canvas.toDataURL('image/png'), 'JPEG', 10, hl, 75, 65);
                });

            doc.setFontSize(11);
            doc.setFont('helvetica', 'normal');
            doc.setTextColor(79, 79, 79);
            infoText = 'The information of the chart is shown in the following table.';
            var splitText = doc.splitTextToSize(infoText, 110);
            var y = 6;
            for (var i=0; i<splitText.length; i++){
                doc.text(90, hl + y, splitText[i]);
                y = y + 4;
            }

            // Information table
            if (this.gathered['keybase']['result'][4]['graphic'][1]['devices']) {
                let headTable = [];
                let bodyTable = [];
                let elem = [];
                let i: any;
                let list = this.gathered['keybase']['result'][4]['graphic'][1]['devices'];
                
                for (let i in list) {
                    if (list[i]['title'] != 'Devices' && list[i]['subtitle']) {
                        if (Number(i) < 8) {
                            elem = [list[i]['title'], list[i]['subtitle']];
                            bodyTable.push(elem);
                        }
                    }
                }

                doc.autoTable({
                    startY: hl + 11,
                    margin: {left: 90},
                    showHead: false,
                    styles: { overflow: 'hidden' },
                    bodyStyles: {
                        fillColor: [52, 73, 94],
                        textColor: 240
                    },
                    alternateRowStyles: {
                        fillColor: [74, 96, 117]
                    },
                    head: [
                        ['Name', 'Value'],
                    ],
                    body: bodyTable,
                });
            }
            hl = hl + 70;
        }

        hl = hl + 10; // Space between modules

        // Leaks module report
        if (this.gathered['leaks'] && this.gathered['leaks']['result'] &&
               this.gathered['leaks']['result'].length > 3) {
            moduleHeight = 80;

            // Validate pageHeight
            if ( hl + moduleHeight > pageHeight) {
                doc.addPage();
                hl = 20;
            }

            // Leaks
            doc.setFontSize(11);
            doc.setDrawColor(44, 93, 126);
            doc.setFillColor(44, 93, 126);
            doc.rect(10, hl, 190, 7, 'F');
            doc.setTextColor(255, 255, 255);
            doc.text('Module leaks', 105, hl + 5, null, null, 'center');
            hl = hl + 10;

            var svg = this.nbCardContainer.nativeElement.querySelector("#divLeakSocial");
            await html2canvas(svg.children[0], { 
                scale: 1,
                useCORS: true, 
                // foreignObjectRendering: true,  // Render with the background but only if the div is in the screen
                async: true,
                logging: true,
                backgroundColor: "#51A5D7",
                allowTaint: true,
                removeContainer: true
                })
                .then(function (canvas) { 
                    doc.addImage(canvas.toDataURL('image/png'), 'JPEG', 10, hl, 75, 65);
                });

            doc.setFontSize(11);
            doc.setFont('helvetica', 'normal');
            doc.setTextColor(79, 79, 79);
            infoText = 'The information of the chart is shown in the following table.';
            var splitText = doc.splitTextToSize(infoText, 110);
            var y = 6;
            for (var i=0; i<splitText.length; i++){
                doc.text(90, hl + y, splitText[i]);
                y = y + 4;
            }

            // Information table
            if (this.gathered['leaks']['result'][4]['graphic'][0]['leaks']) {
                let headTable = [];
                let bodyTable = [];
                let elem = [];
                let i: any;
                let list = this.gathered['leaks']['result'][4]['graphic'][0]['leaks'];
                
                for (let i in list) {
                    if (list[i]['title'] != 'Leaks' && list[i]['subtitle']) {
                        if (Number(i) < 8) {
                            elem = [list[i]['title'], list[i]['subtitle']];
                            bodyTable.push(elem);
                        }
                    }
                }

                doc.autoTable({
                    startY: hl + 11,
                    margin: {left: 90},
                    showHead: false,
                    styles: { overflow: 'hidden' },
                    bodyStyles: {
                        fillColor: [52, 73, 94],
                        textColor: 240
                    },
                    alternateRowStyles: {
                        fillColor: [74, 96, 117]
                    },
                    head: [
                        ['Leak', 'Breach Date'],
                    ],
                    body: bodyTable,
                });
            }

            hl = hl + 70;
        }

        doc.addPage();
        hl = 20;
        // Profile
        for (let i in this.gathered) {
            console.log("i", i)
          for (let j in this.gathered[i]) {
            for (let k in this.gathered[i][j]) {
              for (let l in this.gathered[i][j][k]) {
                if (l == "profile") {
                  for (let p in this.gathered[i][j][k][l]) {
                    this.profile.push(this.gathered[i][j][k][l][p]);
                    for (let q in this.gathered[i][j][k][l][p]) {
                      switch(q) {
                        case 'name':
                        case 'firstName':
                        case 'lastName':
                          console.log("i", this.gathered[i][j][k][l][p][q]);
                          console.log("i prima", i)
                          if (this.gathered[i][j][k][l][p][q] != null) {
                              this.name.push({"label" : this.gathered[i][j][k][l][p][q], "source" : i});
                          };
                          break;
                        case 'photos':
                          for (let iphoto in this.gathered[i][j][k][l][p][q]) {
                              this.photo.push(this.gathered[i][j][k][l][p][q][iphoto]);
                          };    
                          break;
                        case 'social':
                          for (let isocial in this.gathered[i][j][k][l][p][q]) {
                              this.social.push(this.gathered[i][j][k][l][p][q][isocial]);
                          };    
                          break;
                        case 'location':
                          this.location.push({"label" : this.gathered[i][j][k][l][p][q], "source" : i});
                          break;
                        case 'organization':
                          if (Array.isArray(this.gathered[i][j][k][l][p][q])) {
                              for (let r in this.gathered[i][j][k][l][p][q]) {
                                  this.organization.push({"label" : this.gathered[i][j][k][l][p][q][r]['name'], "source" : i});
                              }

                          } else {
                              this.organization.push({"label" : this.gathered[i][j][k][l][p][q], "source" : i});
                          }    
                          break;
                        case 'gender':
                          this.gender.push({"label" : this.gathered[i][j][k][l][p][q], "source" : i});
                          break;
                        default:
                          // code block
                      }
                    }
                  }
                }
              }
            }
          }
        }     

        console.log("Profile name", this.name);
        console.log("Profile location", this.location);
        console.log("Profile gender", this.gender);
        console.log("Profile social", this.social);
        console.log("Profile photo", this.photo);
        console.log("Profile orgnization", this.organization);

        doc.setFontSize(11);
        doc.setDrawColor(32, 61, 79);
        doc.setFillColor(32, 61, 79);
        doc.rect(10, hl, 190, 7, 'F');
        doc.setTextColor(255, 255, 255);
        doc.text('Profile', 105, hl + 5, null, null, 'center');

        hl = 35;

        // Photos
        // console.log("Convirtiendo : ", this.photo[0]['picture']);
        // var oImg = document.createElement("img");
        // oImg.setAttribute('src', this.photo[5]['picture']);
        // oImg.setAttribute('alt', 'na');
        // oImg.setAttribute('height', '250px');
        // oImg.setAttribute('width', '250px');
        // document.body.appendChild(oImg);

        // await html2canvas(oImg, { 
        //     scale: 1,
        //     useCORS: true, 
        //     // allowTaint: true,
        //     // foreignObjectRendering: true,  // Render with the background but only if the div is in the screen
        //     async: true,
        //     logging: true,
        //     // backgroundColor: null,
        //     removeContainer: true
        //     })
        //     .then(function (canvas) { 
        //         console.log("CANVAS DE LA IMAGE", canvas);
        //         doc.addImage(canvas.toDataURL('image/png'), 'JPEG', 10, hl, 75, 65);
        //     });

        // var oImg = document.createElement("img");
        // oImg.setAttribute('src', this.photo[5]['picture']);
        // oImg.setAttribute('alt', 'na');
        // oImg.setAttribute('height', '250px');
        // oImg.setAttribute('width', '250px');
        // document.body.appendChild(oImg);

        // await html2canvas(oImg, { 
        //     scale: 1,
        //     useCORS: true, 
        //     // allowTaint: true,
        //     // foreignObjectRendering: true,  // Render with the background but only if the div is in the screen
        //     async: true,
        //     logging: true,
        //     // backgroundColor: null,
        //     removeContainer: true
        //     })
        //     .then(function (canvas) { 
        //         console.log("CANVAS DE LA IMAGE", canvas);
        //         doc.addImage(canvas.toDataURL('image/png'), 'JPEG', 60, hl, 75, 65);
        //     });

        // doc.addPage();
        // hl = 20;
        // Names
        if (this.name.length > 0) {
            let headTable = [];
            let bodyTable = [];
            let elem = [];
            let list = this.name;
            
            for (let i in list) {
                elem = [list[i]['label'], list[i]['source']];
                bodyTable.push(elem);
            }
            headTable = [['title']]
            headTable[0][0] = {content: 'Names', colSpan: 2, styles: {halign: 'center', fillColor: [22, 160, 133]}};
            doc.autoTable({
                columnStyles: {0: {cellWidth: 50}},
                startY: hl,
                head: headTable, 
                body: bodyTable,
            });
            let finalY = doc.previousAutoTable.finalY;
            hl = finalY;
        }
        // Gender
        if (this.gender.length > 0) {
            let headTable = [];
            let bodyTable = [];
            let elem = [];
            let list = this.gender;
            
            for (let i in list) {
                elem = [list[i]['label'], list[i]['source']];
                bodyTable.push(elem);
            }
            headTable = [['title']]
            headTable[0][0] = {content: 'Gender', colSpan: 2, styles: {halign: 'center', fillColor: [22, 160, 133]}};
            doc.autoTable({
                columnStyles: {0: {cellWidth: 50}},
                startY: hl,
                head: headTable, 
                body: bodyTable,
            });
            let finalY = doc.previousAutoTable.finalY;
            hl = finalY;
        }
        // Location
        if (this.location.length > 0) {
            let headTable = [];
            let bodyTable = [];
            let elem = [];
            let list = this.location;
            
            for (let i in list) {
                elem = [list[i]['label'], list[i]['source']];
                bodyTable.push(elem);
            }
            headTable = [['title']]
            headTable[0][0] = {content: 'Location', colSpan: 2, styles: {halign: 'center', fillColor: [22, 160, 133]}};
            doc.autoTable({
                columnStyles: {0: {cellWidth: 50}},
                startY: hl,
                head: headTable, 
                body: bodyTable,
            });
            let finalY = doc.previousAutoTable.finalY;
            hl = finalY;
        }
        // Organization
        if (this.organization.length > 0) {
            let headTable = [];
            let bodyTable = [];
            let elem = [];
            let list = this.organization;
            
            for (let i in list) {
                elem = [list[i]['label'], list[i]['source']];
                bodyTable.push(elem);
            }
            headTable = [['title']]
            headTable[0][0] = {content: 'Organization', colSpan: 2, styles: {halign: 'center', fillColor: [22, 160, 133]}};
            doc.autoTable({
                columnStyles: {0: {cellWidth: 50}},
                startY: hl,
                head: headTable, 
                body: bodyTable,
            });
            let finalY = doc.previousAutoTable.finalY;
            hl = finalY;
        }

        doc.addPage();
        hl = 20;
        // Timeline
        for (let i in this.gathered) {
          for (let j in this.gathered[i]) {
            for (let k in this.gathered[i][j]) {
              for (let l in this.gathered[i][j][k]) {
                if (l == "timeline") {
                  for (let t in this.gathered[i][j][k][l]) {
                    this.timeline.push(this.gathered[i][j][k][l][t]);
                  }
                }
              }
            }
          }
        }     

        // TODO : Normalize dates
        this.timeline.sort(function(a, b){
            var dateA=a.date.toLowerCase(), dateB=b.date.toLowerCase()
            if (dateA > dateB) //sort string ascending
                return -1 
            if (dateA < dateB)
                return 1
            return 0 
        })

        doc.setFontSize(11);
        doc.setDrawColor(32, 61, 79);
        doc.setFillColor(32, 61, 79);
        doc.rect(10, hl, 190, 7, 'F');
        doc.setTextColor(255, 255, 255);
        doc.text('Timeline', 105, hl + 5, null, null, 'center');

        hl = 35;

        for (let i in this.timeline) {
            hl = hl + 5;
            doc.setFillColor(58, 127, 168);
            doc.setDrawColor(58, 127, 168);
            // doc.setTextColor(79, 79, 79);
            // doc.line(50, hl, 50, hl + 15);
            doc.circle(50, hl + 10, 2, 'F');
            // Information table
            let headTable = [[this.timeline[i]['date']]];
            let bodyTable = [[this.timeline[i]['action'] + ' - ' + [this.timeline[i]['desc']]]];

            doc.autoTable({
                startY: hl + 10,
                margin: {left: 60, right: 40},
                showHead: true,
                styles: { overflow: 'linebreak' },
                bodyStyles: {
                    fillColor: [52, 73, 94],
                    textColor: 240
                },
                alternateRowStyles: {
                    fillColor: [74, 96, 117]
                },
                head: headTable,
                body: bodyTable,
            });

            doc.setFillColor(58, 127, 168);
            doc.setDrawColor(58, 127, 168);
            doc.line(50, hl, 50, doc.previousAutoTable.finalY + 5);
            hl = doc.previousAutoTable.finalY;
            // Validate pageHeight
            if ( hl + 50 > pageHeight) {
                doc.addPage();
                hl = 20;
                doc.setFontSize(11);
                doc.setDrawColor(32, 61, 79);
                doc.setFillColor(32, 61, 79);
                doc.rect(10, hl, 190, 7, 'F');
                doc.setTextColor(255, 255, 255);
                doc.text('Timeline', 105, hl + 5, null, null, 'center');

                hl = 35;
            }
        }

        // doc.text(this.timeline[i]['date'] + ' - ' + , 60, hl + 10, null, null, 'left');
        // hl = hl + 30;
        // TODO addPage
        
        doc.save('Report_iKy_' + this.gathered['email'] + '_' + Date.now() + '.pdf');
        this.processing = false;
    }
}
