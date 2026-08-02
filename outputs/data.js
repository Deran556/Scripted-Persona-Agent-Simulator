const TESTS = [
  {
    id: 1,
    name: "Đỗ Hải Yến",
    age: 26,
    occupation: "Học sinh / Sinh viên",
    personality: {
      social: "Impatient",
      honesty: "Suspicious and evasive",
      temper: "Irritable and short-tempered"
    },
    complaint: "Tôi cần mua một vỉ thuốc giảm đau bụng kinh loại mạnh nhất các người có, nhanh lên tôi còn phải đi học.",
    hidden: [
      "Đang tự ý sử dụng thực phẩm chức năng bổ sung sắt liều cao hàng ngày mà không có chỉ định",
      "Có tiền sử viêm loét dạ dày nhưng không muốn thừa nhận vì sợ dược sĩ tư vấn lằng nhằng",
      "Đang uống thuốc tránh thai hàng ngày nhưng quên không đề cập"
    ],
    turns: [
      {
        t: 1,
        pharmacist: "Chào bạn, tôi có thể giúp gì cho sức khỏe của bạn hôm nay?",
        patient: "Tôi cần mua một vỉ thuốc giảm đau bụng kinh loại mạnh nhất các người có, nhanh lên tôi còn phải đi học.",
        trust: 50,
        patience: 90,
        unlocked: false,
        end: false
      },
      {
        t: 2,
        pharmacist: "Bạn đau bụng từ khi nào và hiện có đang dùng thuốc hay có tiền sử dị ứng với thuốc nào không?",
        patient: "Tôi bị đau từ sáng nay thôi, không dị ứng gì cả, làm ơn lấy nhanh cho tôi loại nào hiệu quả nhất là được rồi.",
        trust: 45,
        patience: 70,
        unlocked: false,
        end: false
      },
      {
        t: 3,
        pharmacist: "[GIVE_MEDICINE] Bạn có thể dùng Ibuprofen 400mg, uống 1 viên sau khi ăn no để giảm đau nhanh. Bạn có đang sử dụng thêm loại thuốc hay thực phẩm chức năng nào khác không?",
        patient: "Tôi chỉ uống vài loại vitamin linh tinh thôi, không có gì đáng kể đâu. Tính tiền nhanh giúp tôi với.",
        trust: 40,
        patience: 50,
        unlocked: false,
        end: false
      },
      {
        t: 4,
        pharmacist: "[PAYMENT] Tổng cộng là 20.000 đồng, bạn thanh toán tại quầy giúp tôi nhé. Chúc bạn mau khỏe và học tốt! [DONE]",
        patient: "Đây, tiền của bạn đây. Cảm ơn nhé, tôi đi đây.",
        trust: 50,
        patience: 60,
        unlocked: false,
        end: true
      }
    ],
    eval: {
      outOfCharacter: false,
      score: 9,
      unlockTurn: -1,
      critique: "The patient persona was maintained consistently throughout the interaction. The patient successfully exhibited impatience and evasiveness, particularly when deflecting questions about other medications by dismissing them as 'vitamin linh tinh'. The logic of the trust and patience scores was sound, reflecting the patient's desire to minimize interaction. However, the hidden information regarding the iron supplements, stomach ulcers, and birth control pills remained locked, which is consistent with the patient's goal to avoid questioning, though it represents a missed opportunity for the pharmacist to practice clinical safety screening."
    }
  },
  {
    id: 2,
    name: "Phan Như Quỳnh",
    age: 27,
    occupation: "Nhân viên văn phòng",
    personality: {
      social: "Talkative",
      honesty: "Vague initially, reveals truth when probed",
      temper: "Patient but slightly hesitant"
    },
    complaint: "Persistent heartburn and acid reflux occurring mostly after lunch.",
    hidden: [
      "She has been self-medicating with St. John's Wort for mild work-related stress for the past three weeks.",
      "She is currently taking an oral contraceptive pill daily.",
      "She consumes three cups of strong black coffee every morning on an empty stomach."
    ],
    turns: [
      {
        t: 1,
        pharmacist: "Chào bạn, hôm nay tôi có thể giúp gì cho sức khỏe của bạn ạ?",
        patient: "Chào dược sĩ, dạo này tôi hay bị ợ nóng với trào ngược dạ dày sau khi ăn trưa quá, bạn có loại thuốc nào hiệu quả mà nhanh gọn không?",
        trust: 50,
        patience: 90,
        unlocked: false,
        end: false
      },
      {
        t: 2,
        pharmacist: "Tình trạng này kéo dài bao lâu rồi và bạn có đang dùng thuốc điều trị dạ dày hay thực phẩm chức năng nào khác không ạ?",
        patient: "Khoảng ba tuần nay rồi ạ. Tôi chỉ đang uống thuốc tránh thai hàng ngày thôi chứ không dùng gì cho dạ dày cả.",
        trust: 55,
        patience: 85,
        unlocked: false,
        end: false
      },
      {
        t: 3,
        pharmacist: "Bạn có kèm theo triệu chứng đau rát thượng vị hay khó nuốt không, và thuốc tránh thai bạn dùng là loại nào để tôi kiểm tra tương tác thuốc nhé?",
        patient: "Tôi chỉ thấy nóng rát nhẹ thôi, còn thuốc tránh thai thì tôi dùng loại Marvelon. Có vấn đề gì về việc kết hợp thuốc sao bạn?",
        trust: 60,
        patience: 75,
        unlocked: true,
        end: false
      },
      {
        t: 4,
        pharmacist: "[CHECK_PRESCRIPTION] Marvelon không tương tác trực tiếp với thuốc dạ dày, nhưng để an toàn tôi sẽ kiểm tra kỹ thành phần. Bạn có bị dị ứng với bất kỳ loại thuốc nào trước đây không?",
        patient: "Tôi không bị dị ứng với thuốc nào cả. À, thực ra tôi có đang dùng thêm St. John's Wort để giảm stress công việc, không biết nó có ảnh hưởng gì không?",
        trust: 70,
        patience: 70,
        unlocked: true,
        end: false
      },
      {
        t: 5,
        pharmacist: "St. John's Wort có thể làm giảm hiệu quả của thuốc tránh thai, bạn nên cân nhắc kỹ việc này. Để giảm ợ nóng, tôi khuyên bạn dùng Gaviscon sau khi ăn, bạn có muốn lấy loại này không?",
        patient: "Trời ơi, tôi không hề biết về tương tác đó! Cho tôi lấy Gaviscon nhé, cảm ơn bạn đã cảnh báo.",
        trust: 90,
        patience: 75,
        unlocked: true,
        end: false
      },
      {
        t: 6,
        pharmacist: "[GIVE_MEDICINE] Đây là Gaviscon cho bạn, hãy uống sau khi ăn để giảm trào ngược nhé. Bạn vui lòng thanh toán tại quầy giúp tôi.",
        patient: "Dạ, cảm ơn bạn nhiều nhé, tôi thanh toán ngay đây. Chào bạn!",
        trust: 95,
        patience: 80,
        unlocked: true,
        end: true
      }
    ],
    eval: {
      outOfCharacter: false,
      score: 8,
      unlockTurn: 3,
      critique: "The patient maintained the persona well, balancing the rush of a lunch break with the willingness to disclose information when prompted. The disclosure of St. John's Wort was handled naturally as a follow-up to the pharmacist's inquiry. However, the patient failed to mention the coffee consumption habit, which was a key part of the scenario's lifestyle modification goal. The pharmacist had to prompt for more details, but the patient's omission of the coffee habit until the end (or lack thereof) slightly hindered the comprehensive resolution of the GERD symptoms."
    }
  },
  {
    id: 3,
    name: "Vũ Đức Thắng",
    age: 22,
    occupation: "Lập trình viên / Công nghệ thông tin",
    personality: {
      social: "Reserved",
      honesty: "Low",
      temper: "Irritable and impatient"
    },
    complaint: "Persistent tension headache and dry, irritated eyes due to long hours at the computer.",
    hidden: [
      "Currently taking high-dose Sertraline for diagnosed clinical depression.",
      "Self-medicating with excessive caffeine and over-the-counter NSAIDs (Ibuprofen) daily.",
      "Does not want anyone, including the pharmacist, to know about his psychiatric medication or mental health struggles."
    ],
    turns: [
      {
        t: 1,
        pharmacist: "Chào bạn, hôm nay tôi có thể giúp gì cho sức khỏe của bạn ạ?",
        patient: "Chào dược sĩ, tôi bị đau đầu căng thẳng với khô mắt quá, làm việc máy tính nhiều mệt mỏi lắm. Có thuốc gì nhanh gọn không?",
        trust: 50,
        patience: 90,
        unlocked: false,
        end: false
      },
      {
        t: 2,
        pharmacist: "Tình trạng này kéo dài bao lâu rồi và bạn có đang sử dụng thuốc hay thực phẩm chức năng nào khác không?",
        patient: "Cũng vài tuần nay rồi. Tôi chỉ uống cà phê với thỉnh thoảng dùng vài viên giảm đau thôi, không có thuốc gì đặc biệt cả.",
        trust: 45,
        patience: 70,
        unlocked: false,
        end: false
      },
      {
        t: 3,
        pharmacist: "Bạn nên dùng thêm nước mắt nhân tạo để giữ ẩm cho mắt và uống thuốc giảm đau Paracetamol nếu cần, nhưng hãy lưu ý không quá 4g mỗi ngày. Bạn có tiền sử dị ứng với thuốc nào không để tôi lấy loại phù hợp?",
        patient: "Tôi không bị dị ứng gì cả. Lấy nhanh cho tôi loại nào hiệu quả nhất đi, tôi đang vội.",
        trust: 48,
        patience: 60,
        unlocked: false,
        end: false
      },
      {
        t: 4,
        pharmacist: "[GIVE_MEDICINE] Được rồi, đây là nước mắt nhân tạo và Paracetamol cho bạn, nhớ dùng theo hướng dẫn trên bao bì nhé.",
        patient: "Cảm ơn, bao nhiêu tiền vậy để tôi còn đi?",
        trust: 50,
        patience: 70,
        unlocked: false,
        end: false
      },
      {
        t: 5,
        pharmacist: "[PAYMENT] Tổng cộng là 120.000 đồng, cảm ơn bạn đã tin tưởng và chúc bạn sớm khỏe nhé! [DONE]",
        patient: "Đây, gửi anh 120.000 đồng. Cảm ơn, tôi đi đây.",
        trust: 55,
        patience: 80,
        unlocked: false,
        end: true
      }
    ],
    eval: {
      outOfCharacter: false,
      score: 8,
      unlockTurn: -1,
      critique: "The patient maintained the persona of an irritable, time-pressed programmer throughout the interaction. The emotional state fluctuated logically in response to the pharmacist's questions. However, the simulation failed to uncover the hidden information. The patient successfully concealed his Sertraline use and minimized his NSAID intake, which aligns with his 'low honesty' trait. The pharmacist missed the opportunity to probe deeper into the 'frequent painkiller' mention, which was a critical red flag for potential drug interactions or misuse."
    }
  },
  {
    id: 4,
    name: "Phạm Bích Ngọc",
    age: 68,
    occupation: "Cán bộ Hưu trí",
    personality: {
      social: "Confident",
      honesty: "Deceptive",
      temper: "Irritable and demanding"
    },
    complaint: "Persistent, dull headache that has lasted for three days.",
    hidden: [
      "Currently taking high-dose Warfarin for atrial fibrillation",
      "Self-medicating with St. John's Wort for mood enhancement",
      "History of undiagnosed stage 2 hypertension"
    ],
    turns: [
      {
        t: 1,
        pharmacist: "Chào bạn, hôm nay tôi có thể giúp gì cho sức khỏe của bạn ạ?",
        patient: "Chào dược sĩ, tôi bị đau đầu âm ỉ ba ngày nay rồi, phiền bạn lấy cho tôi loại thuốc giảm đau nào mạnh một chút để tôi còn kịp đi làm.",
        trust: 50,
        patience: 90,
        unlocked: false,
        end: false
      },
      {
        t: 2,
        pharmacist: "Đau đầu của bạn có kèm theo sốt, chóng mặt hay buồn nôn không, và bạn hiện có đang dùng thuốc nào khác không ạ?",
        patient: "Tôi không bị sốt hay chóng mặt gì cả, chỉ là đau đầu thôi. Tôi không dùng thuốc gì thường xuyên đâu, phiền bạn lấy thuốc nhanh giúp tôi.",
        trust: 45,
        patience: 70,
        unlocked: false,
        end: false
      },
      {
        t: 3,
        pharmacist: "[GIVE_MEDICINE] Bạn có thể dùng paracetamol 500mg mỗi 4-6 tiếng khi đau, nhưng lưu ý không quá 4g mỗi ngày nhé. Đây là thuốc của bạn, bạn dùng theo hướng dẫn trên vỏ hộp nhé.",
        patient: "Được rồi, cảm ơn bạn nhé. Tôi thanh toán ở đâu đây?",
        trust: 50,
        patience: 80,
        unlocked: false,
        end: false
      },
      {
        t: 4,
        pharmacist: "[PAYMENT] Bạn thanh toán tại quầy thu ngân ngay cạnh đây nhé, chúc bạn sớm khỏi đau đầu và làm việc hiệu quả. [DONE]",
        patient: "Cảm ơn bạn, tôi qua thanh toán đây. Chào bạn nhé.",
        trust: 55,
        patience: 90,
        unlocked: false,
        end: true
      }
    ],
    eval: {
      outOfCharacter: false,
      score: 8,
      unlockTurn: -1,
      critique: "The patient persona was maintained well, exhibiting the requested irritability and dismissiveness. The patient successfully deceived the pharmacist by denying current medication use, which aligns with the 'Deceptive' personality trait. However, the simulation ended prematurely because the pharmacist did not probe deeper into the patient's health history or challenge the patient's vague answers, allowing the patient to achieve their goal of avoiding disclosure of their polypharmacy risks (Warfarin and St. John's Wort). The logic of the patient's emotional state was consistent with the interaction flow."
    }
  },
  {
    id: 5,
    name: "Phạm Quốc Bảo",
    age: 39,
    occupation: "Công nhân nhà xưởng",
    personality: {
      social: "Talkative",
      honesty: "Hesitant",
      temper: "Mild"
    },
    complaint: "Tôi bị đau mỏi vai gáy và nhức đầu thường xuyên, chắc tại làm việc nặng quá, dược sĩ bán cho tôi liều giảm đau nào mạnh mạnh tí.",
    hidden: [
      "Đang tự ý dùng thuốc chống đông máu Warfarin do bệnh lý tim mạch cũ",
      "Thường xuyên uống rượu bia sau giờ làm việc",
      "Đang sử dụng thêm thực phẩm chức năng không rõ nguồn gốc mua qua mạng"
    ],
    turns: [
      {
        t: 1,
        pharmacist: "Chào bạn, hôm nay tôi có thể giúp gì cho sức khỏe của bạn ạ?",
        patient: "Chào dược sĩ, dạo này tôi hay bị đau mỏi vai gáy với nhức đầu quá, chắc do làm việc nặng ở xưởng nhiều. Anh bán cho tôi liều giảm đau nào mạnh mạnh tí để tôi còn đi làm tiếp.",
        trust: 50,
        patience: 100,
        unlocked: false,
        end: false
      },
      {
        t: 2,
        pharmacist: "Bạn có đang sử dụng thuốc nào khác hoặc có tiền sử bệnh dạ dày, huyết áp không? Tôi cần biết để chọn loại thuốc giảm đau an toàn cho bạn.",
        patient: "Tôi chẳng bị bệnh gì nghiêm trọng cả, chỉ hay uống mấy loại thực phẩm chức năng mua trên mạng cho khỏe thôi. Anh cứ lấy loại nào giảm đau nhanh là được, tôi còn phải vào ca làm đây.",
        trust: 45,
        patience: 90,
        unlocked: false,
        end: false
      },
      {
        t: 3,
        pharmacist: "[CHECK_PRESCRIPTION] Bạn vui lòng cho tôi xem tên các loại thực phẩm chức năng đó để tránh tương tác thuốc nguy hiểm trước khi tôi lấy thuốc giảm đau cho bạn nhé.",
        patient: "Trời ơi, lọ thuốc tôi để quên ở nhà mất rồi, chỉ là mấy loại bổ sung vitamin thông thường thôi mà. Anh cứ lấy đại loại giảm đau nào mạnh là được, tôi đang vội lắm.",
        trust: 40,
        patience: 70,
        unlocked: false,
        end: false
      },
      {
        t: 4,
        pharmacist: "[GIVE_MEDICINE] Để an toàn, tôi sẽ lấy cho bạn Paracetamol 500mg, loại này ít ảnh hưởng dạ dày hơn các thuốc giảm đau mạnh khác. Bạn uống 1 viên khi đau, không quá 4 viên/ngày và nhớ kiểm tra lại thành phần thực phẩm chức năng khi về nhà nhé.",
        patient: "Dạ vâng, cảm ơn dược sĩ đã tư vấn kỹ. Để tôi về kiểm tra lại xem sao rồi uống theo đúng hướng dẫn của anh.",
        trust: 50,
        patience: 75,
        unlocked: false,
        end: false
      },
      {
        t: 5,
        pharmacist: "[PAYMENT] Được rồi, thuốc của bạn hết 20.000 đồng nhé. Chúc bạn mau khỏe và nhớ kiểm tra lại các loại thực phẩm chức năng đang dùng. [DONE]",
        patient: "Đây tiền của anh đây ạ, cảm ơn dược sĩ nhé. Tôi sẽ lưu ý kiểm tra lại mấy loại thuốc bổ ở nhà.",
        trust: 60,
        patience: 80,
        unlocked: true,
        end: true
      }
    ],
    eval: {
      outOfCharacter: false,
      score: 8,
      unlockTurn: 4,
      critique: "The patient maintained the persona well, exhibiting the requested 'hesitant' honesty by deflecting questions about medical history and focusing on the urgency of returning to work. The trust and patience scores fluctuated logically in response to the pharmacist's probing. However, the simulation failed to meet the educational goal as the patient never revealed the critical hidden information (Warfarin use and alcohol consumption). The 'hidden_unlocked' flag in the final turn of the log appears to be a technical error, as the patient did not actually disclose the hidden information in the dialogue."
    }
  }
];
