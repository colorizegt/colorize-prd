import { Component, xml } from "@odoo/owl";

export class discountLogNote extends Component {
    static template = 'chris.discountLogNote';
    setup() {
        super.setup(...arguments);
        this.discount_reason = self.posmodel.getOrder().discount_reason || ''
        this.discount_reason_file = self.posmodel.getOrder().discount_reason_file || ''
    }
    applyFixedDiscount(ev){
        this.setDiscountReason(ev)
        self.posmodel.productScreen.opennumpad(this.props.selectedLine);
        this.props.close();
    }
    applyPercentageDiscount(ev){
        this.setDiscountReason()
        self.posmodel.productScreen.numberBuffer.reset();
        this.props.close();
    }
    onchangeDiscountReasonText(ev){
        this.discount_reason = ev.target.value
    }
    async onchangeDiscountReason(ev){
        var fileData = await this.fileToBase64(ev.target.files[0])
        this.discount_reason_file = fileData
        this.discount_reason_file_name = ev.target.files[0].name
    }
    setDiscountReason(){
        var dis_reason = this.discount_reason;
        if (dis_reason != ''){
            self.posmodel.getOrder().setDiscountReason(dis_reason);
        }
        if (this.discount_reason_file != ''){
            self.posmodel.getOrder().setDiscountFile(this.discount_reason_file);
            self.posmodel.getOrder().setDiscountFileName(this.discount_reason_file_name);
        }
    }
    fileToBase64(file) {
        return new Promise((resolve) => {
            const reader = new FileReader();
            reader.onload = () => resolve(reader.result.split(",")[1]);
            reader.readAsDataURL(file);
        });
    }
}